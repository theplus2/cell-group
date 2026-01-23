"""
교인 소그룹 자동 편성 시스템 - GUI 애플리케이션
PyQt6 기반 데스크탑 앱
"""

import sys
import os
from pathlib import Path
from typing import Optional, List, Set

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpinBox, QFileDialog, QTableWidget,
    QTableWidgetItem, QProgressBar, QGroupBox, QMessageBox,
    QFrame, QSplitter, QHeaderView, QStatusBar, QTabWidget,
    QComboBox, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QDragEnterEvent, QDropEvent

# 프로젝트 모듈 임포트
sys.path.insert(0, str(Path(__file__).parent))
from src.data_loader import DataLoader
from src.preprocessor import DataPreprocessor
from src.sorter import GroupSorter
from src.config import SorterConfig
from src.constraints import Constraint, ConstraintType, ConstraintManager


class SortingWorker(QThread):
    """백그라운드에서 소그룹 편성 작업을 수행하는 워커 스레드"""
    
    progress = pyqtSignal(int, str)  # (진행률, 상태 메시지)
    finished = pyqtSignal(object, object)  # (결과 DataFrame, 통계 DataFrame)
    error = pyqtSignal(str)  # 에러 메시지
    
    def __init__(
        self, 
        file_path: str, 
        group_size: int, 
        age_tolerance: int,
        constraint_manager: Optional[ConstraintManager] = None
    ):
        super().__init__()
        self.file_path = file_path
        self.group_size = group_size
        self.age_tolerance = age_tolerance
        self.constraint_manager = constraint_manager
    
    def run(self):
        try:
            # 1. 데이터 로드
            self.progress.emit(10, "데이터 로드 중...")
            loader = DataLoader()
            df = loader.load_file(self.file_path)
            
            # 2. 컬럼 검증
            self.progress.emit(20, "데이터 검증 중...")
            is_valid, missing = loader.validate_columns()
            if not is_valid:
                self.error.emit(f"필수 컬럼 누락: {', '.join(missing)}")
                return
            
            # 3. 데이터 전처리
            self.progress.emit(40, "데이터 전처리 중...")
            preprocessor = DataPreprocessor(df)
            processed_df = preprocessor.process()
            
            # 4. 소그룹 편성
            self.progress.emit(60, "소그룹 편성 중...")
            sorter = GroupSorter(
                processed_df,
                group_size=self.group_size,
                age_tolerance=self.age_tolerance,
                constraint_manager=self.constraint_manager
            )
            result_df = sorter.sort_into_groups()
            
            # 5. 통계 생성
            self.progress.emit(80, "통계 생성 중...")
            stats_df = sorter.get_group_statistics()
            
            # 제약조건 위반 검사
            violations = sorter.get_constraint_violations()
            if violations:
                self.progress.emit(90, f"⚠️ 제약조건 위반 {len(violations)}건 발견")
            
            self.progress.emit(100, "완료!")
            self.finished.emit(result_df, stats_df)
            
        except Exception as e:
            self.error.emit(str(e))


class ConstraintsTab(QWidget):
    """제약 조건 관리 탭"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.constraint_manager = ConstraintManager()
        self.loaded_names: Set[str] = set()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 입력 폼
        form_group = QGroupBox("제약 조건 추가")
        form_layout = QHBoxLayout(form_group)
        
        # 유형 선택
        form_layout.addWidget(QLabel("유형:"))
        self.type_combo = QComboBox()
        for ct in ConstraintType:
            self.type_combo.addItem(ct.value)
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
        form_layout.addWidget(self.type_combo)
        
        # 대상1
        form_layout.addWidget(QLabel("대상1:"))
        self.person1_combo = QComboBox()
        self.person1_combo.setEditable(True)
        self.person1_combo.setMinimumWidth(100)
        form_layout.addWidget(self.person1_combo)
        
        # 대상2
        self.person2_label = QLabel("대상2:")
        form_layout.addWidget(self.person2_label)
        self.person2_combo = QComboBox()
        self.person2_combo.setEditable(True)
        self.person2_combo.setMinimumWidth(100)
        form_layout.addWidget(self.person2_combo)
        
        # 추가 버튼
        self.add_btn = QPushButton("추가")
        self.add_btn.clicked.connect(self.add_constraint)
        form_layout.addWidget(self.add_btn)
        
        layout.addWidget(form_group)
        
        # 목록 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["유형", "대상1", "대상2", "메모"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        # 삭제 버튼
        del_layout = QHBoxLayout()
        del_layout.addStretch()
        self.del_btn = QPushButton("선택 항목 삭제")
        self.del_btn.clicked.connect(self.delete_selected)
        del_layout.addWidget(self.del_btn)
        layout.addLayout(del_layout)
        
        # 초기 상태 설정
        self.on_type_changed(0)
        
    def on_type_changed(self, index):
        type_str = self.type_combo.currentText()
        is_leader = (type_str == ConstraintType.LEADER.value)
        self.person2_combo.setEnabled(not is_leader)
        self.person2_label.setEnabled(not is_leader)
        if is_leader:
            self.person2_combo.clearEditText()
            
    def update_names(self, names: Set[str]):
        """이름 목록 업데이트"""
        self.loaded_names = names
        sorted_names = sorted(list(names))
        
        self.person1_combo.clear()
        self.person1_combo.addItems(sorted_names)
        
        self.person2_combo.clear()
        self.person2_combo.addItems(sorted_names)
        
    def set_manager(self, manager: ConstraintManager):
        """외부에서 로드된 매니저 설정"""
        self.constraint_manager = manager
        self.refresh_table()
        
    def refresh_table(self):
        """테이블 갱신"""
        self.table.setRowCount(0)
        for row, c in enumerate(self.constraint_manager.constraints):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(c.type.value))
            self.table.setItem(row, 1, QTableWidgetItem(c.person1))
            self.table.setItem(row, 2, QTableWidgetItem(c.person2 or ""))
            self.table.setItem(row, 3, QTableWidgetItem(c.note))
            
            # 위반 여부 확인 (로드된 이름에 없는 경우 빨간색)
            if self.loaded_names:
                if c.person1 and c.person1 not in self.loaded_names:
                    self.table.item(row, 1).setForeground(QColor("red"))
                    self.table.item(row, 1).setToolTip("명단에 없는 이름입니다")
                if c.person2 and c.person2 not in self.loaded_names:
                    self.table.item(row, 2).setForeground(QColor("red"))
                    self.table.item(row, 2).setToolTip("명단에 없는 이름입니다")

    def add_constraint(self):
        type_str = self.type_combo.currentText()
        p1 = self.person1_combo.currentText().strip()
        p2 = self.person2_combo.currentText().strip()
        
        if not p1:
            QMessageBox.warning(self, "입력 오류", "대상1을 입력해주세요.")
            return
            
        ctype = next(ct for ct in ConstraintType if ct.value == type_str)
        
        if ctype != ConstraintType.LEADER and not p2:
            QMessageBox.warning(self, "입력 오류", "대상2를 입력해주세요.")
            return
            
        if p1 == p2:
            QMessageBox.warning(self, "입력 오류", "대상1과 대상2는 같을 수 없습니다.")
            return
            
        self.constraint_manager.add(Constraint(ctype, p1, p2 if not ctype == ConstraintType.LEADER else None))
        self.refresh_table()
        
    def delete_selected(self):
        rows = sorted(set(index.row() for index in self.table.selectedIndexes()), reverse=True)
        for row in rows:
            self.constraint_manager.remove(row)
        self.refresh_table()


class MainWindow(QMainWindow):
    """메인 윈도우"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("교인 소그룹 자동 편성 시스템 v2.5")
        self.setMinimumSize(1000, 750)
        self.setAcceptDrops(True)
        
        self.input_file = None
        self.result_df = None
        self.stats_df = None
        
        self.setup_ui()
        self.setup_statusbar()
    
    def setup_ui(self):
        """UI 구성"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # === 상단: 파일 선택 영역 ===
        file_group = QGroupBox("📂 데이터 파일")
        file_layout = QHBoxLayout(file_group)
        
        self.file_label = QLabel("파일을 선택하거나 여기에 드래그하세요")
        self.file_label.setStyleSheet("""
            QLabel {
                padding: 20px;
                border: 2px dashed #aaa;
                border-radius: 8px;
                background: #f9f9f9;
                font-size: 14px;
                color: #666;
            }
        """)
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        file_layout.addWidget(self.file_label, 1)
        
        self.browse_btn = QPushButton("파일 선택...")
        self.browse_btn.setMinimumHeight(50)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background: #4a90d9;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
                padding: 10px 25px;
            }
            QPushButton:hover { background: #3a7bc8; }
        """)
        self.browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.browse_btn)
        
        main_layout.addWidget(file_group)
        
        # === 중단: 탭 위젯 (설정 / 제약조건) ===
        self.tabs = QTabWidget()
        
        # 탭 1: 기본 설정
        settings_tab = QWidget()
        settings_layout = QHBoxLayout(settings_tab)
        settings_layout.setSpacing(40)
        
        # 그룹당 인원
        group_size_layout = QVBoxLayout()
        group_size_layout.addWidget(QLabel("그룹당 목표 인원"))
        self.group_size_spin = QSpinBox()
        self.group_size_spin.setRange(3, 50)
        self.group_size_spin.setValue(10)
        self.group_size_spin.setMinimumHeight(40)
        self.group_size_spin.setStyleSheet("font-size: 16px; padding: 5px;")
        group_size_layout.addWidget(self.group_size_spin)
        settings_layout.addLayout(group_size_layout)
        
        # 나이 허용 범위
        age_layout = QVBoxLayout()
        age_layout.addWidget(QLabel("나이 허용 범위 (±N살)"))
        self.age_spin = QSpinBox()
        self.age_spin.setRange(1, 20)
        self.age_spin.setValue(5)
        self.age_spin.setMinimumHeight(40)
        self.age_spin.setStyleSheet("font-size: 16px; padding: 5px;")
        age_layout.addWidget(self.age_spin)
        settings_layout.addLayout(age_layout)
        
        settings_layout.addStretch()
        
        # 실행 버튼
        self.run_btn = QPushButton("🚀 편성 시작")
        self.run_btn.setMinimumSize(150, 50)
        self.run_btn.setEnabled(False)
        self.run_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover { background: #218838; }
            QPushButton:disabled { background: #ccc; }
        """)
        self.run_btn.clicked.connect(self.start_sorting)
        settings_layout.addWidget(self.run_btn)
        
        self.tabs.addTab(settings_tab, "기본 설정")
        
        # 탭 2: 제약 조건
        self.constraints_tab = ConstraintsTab()
        self.tabs.addTab(self.constraints_tab, "제약 조건")
        
        main_layout.addWidget(self.tabs)
        
        # === 진행률 표시 ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(25)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: #28a745;
                border-radius: 4px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        # === 하단: 결과 테이블 ===
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 결과 테이블
        result_group = QGroupBox("📋 편성 결과")
        result_layout = QVBoxLayout(result_group)
        self.result_table = QTableWidget()
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setStyleSheet("""
            QTableWidget {
                font-size: 12px;
                gridline-color: #ddd;
            }
            QHeaderView::section {
                background: #f0f0f0;
                padding: 8px;
                font-weight: bold;
                border: 1px solid #ddd;
            }
        """)
        result_layout.addWidget(self.result_table)
        splitter.addWidget(result_group)
        
        # 통계 테이블
        stats_group = QGroupBox("📊 그룹별 통계")
        stats_layout = QVBoxLayout(stats_group)
        self.stats_table = QTableWidget()
        self.stats_table.setAlternatingRowColors(True)
        self.stats_table.setStyleSheet("""
            QTableWidget {
                font-size: 12px;
                gridline-color: #ddd;
            }
            QHeaderView::section {
                background: #f0f0f0;
                padding: 8px;
                font-weight: bold;
                border: 1px solid #ddd;
            }
        """)
        stats_layout.addWidget(self.stats_table)
        splitter.addWidget(stats_group)
        
        splitter.setSizes([600, 400])
        main_layout.addWidget(splitter, 1)
        
        # === 하단 버튼 ===
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_btn = QPushButton("💾 결과 저장")
        self.save_btn.setEnabled(False)
        self.save_btn.setMinimumSize(120, 40)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #17a2b8;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background: #138496; }
            QPushButton:disabled { background: #ccc; }
        """)
        self.save_btn.clicked.connect(self.save_result)
        button_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(button_layout)
    
    def setup_statusbar(self):
        """상태바 설정"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("파일을 선택하여 시작하세요.")
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """드래그 진입 이벤트"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """드롭 이벤트"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.endswith(('.xlsx', '.csv')):
                self.set_input_file(file_path)
            else:
                QMessageBox.warning(self, "오류", "엑셀(.xlsx) 또는 CSV 파일만 지원합니다.")
    
    def browse_file(self):
        """파일 탐색기 열기"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "교인 명단 파일 선택",
            "",
            "Excel Files (*.xlsx);;CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            self.set_input_file(file_path)
    
    def set_input_file(self, file_path: str):
        """입력 파일 설정"""
        self.input_file = file_path
        filename = Path(file_path).name
        self.file_label.setText(f"📄 {filename}")
        self.file_label.setStyleSheet("""
            QLabel {
                padding: 20px;
                border: 2px solid #28a745;
                border-radius: 8px;
                background: #e8f5e9;
                font-size: 14px;
                color: #2e7d32;
                font-weight: bold;
            }
        """)
        self.run_btn.setEnabled(True)
        self.statusbar.showMessage(f"파일 로드됨: {filename}")
        
        # 파일이 로드되면 이름 목록 추출 및 제약조건 로드
        try:
            loader = DataLoader()
            loader.load_file(file_path)
            
            # 1. 이름 목록 업데이트
            names = loader.get_names()
            self.constraints_tab.update_names(names)
            
            # 2. 제약조건 로드 (제약조건 시트가 있는 경우)
            if loader.has_constraints():
                manager = loader.get_constraint_manager()
                self.constraints_tab.set_manager(manager)
                self.statusbar.showMessage(f"파일 및 제약조건 로드됨 ({len(manager)}건)")
            else:
                # 새 파일 로드 시 제약조건 초기화하고 싶은 경우:
                # self.constraints_tab.set_manager(ConstraintManager())
                # 유지하고 싶은 경우:
                # self.constraints_tab.refresh_table() (이름 유효성 검사 갱신)
                self.constraints_tab.refresh_table()
                
        except Exception as e:
            self.statusbar.showMessage(f"⚠️ 파일 로드 중 경고: {str(e)}")
    
    def start_sorting(self):
        """편성 시작"""
        if not self.input_file:
            return
        
        self.run_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 현재 제약조건 관리자 가져오기
        constraint_manager = self.constraints_tab.constraint_manager
        
        self.worker = SortingWorker(
            self.input_file,
            self.group_size_spin.value(),
            self.age_spin.value(),
            constraint_manager
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def on_progress(self, value: int, message: str):
        """진행률 업데이트"""
        self.progress_bar.setValue(value)
        self.statusbar.showMessage(message)
    
    def on_finished(self, result_df, stats_df):
        """편성 완료"""
        self.result_df = result_df
        self.stats_df = stats_df
        
        # 결과 테이블 채우기 (조별 편성표 형식)
        self.populate_group_table(self.result_table, result_df)
        # 통계 테이블은 기존 방식 유지
        self.populate_table(self.stats_table, stats_df)
        
        self.run_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        num_groups = result_df['소그룹명'].nunique()
        num_members = len(result_df)
        self.statusbar.showMessage(f"✅ 완료! {num_members}명을 {num_groups}개 그룹으로 편성했습니다.")
        
        QMessageBox.information(
            self,
            "편성 완료",
            f"총 {num_members}명을 {num_groups}개 소그룹으로 편성했습니다!"
        )
    
    def on_error(self, message: str):
        """에러 처리"""
        self.run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.statusbar.showMessage(f"❌ 오류: {message}")
        QMessageBox.critical(self, "오류", message)
    
    def populate_group_table(self, table: QTableWidget, df):
        """조별 편성표 형식으로 DataFrame을 QTableWidget에 표시
        
        형식: | 조 | 멤버1 | 멤버2 | 멤버3 | ... |
        """
        table.clear()
        
        if '소그룹명' not in df.columns:
            self.populate_table(table, df)
            return
        
        # 조별로 그룹화
        groups = df.groupby('소그룹명')
        # 조 이름을 숫자 기준으로 오름차순 정렬 (1조, 2조, ..., 10조)
        def extract_group_number(name):
            import re
            match = re.search(r'\d+', str(name))
            return int(match.group()) if match else 0
        group_names = sorted(groups.groups.keys(), key=extract_group_number)
        
        # 가장 많은 인원이 있는 조의 멤버 수 계산
        max_members = max(len(group) for _, group in groups)
        
        # 테이블 설정
        table.setRowCount(len(group_names))
        table.setColumnCount(max_members + 1)  # 조 이름 + 멤버들
        
        # 헤더 설정
        headers = ['조'] + [f'멤버 {i+1}' for i in range(max_members)]
        table.setHorizontalHeaderLabels(headers)
        
        # 데이터 채우기
        for row, group_name in enumerate(group_names):
            # 조 이름
            group_item = QTableWidgetItem(str(group_name))
            group_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            group_item.setBackground(QColor('#e3f2fd'))
            group_item.setFont(QFont('맑은 고딕', 10, QFont.Weight.Bold))
            table.setItem(row, 0, group_item)
            
            # 해당 조의 멤버들 (리더를 맨 앞으로 정렬)
            group_df = groups.get_group(group_name).copy()
            # 리더가 맨 앞에 오도록 정렬: 리더 먼저, 그 다음 일반, 마지막으로 케어 대상
            sort_order = {'리더': 0, '일반': 1, '케어 대상': 2}
            group_df['정렬순서'] = group_df['분류결과'].map(lambda x: sort_order.get(x, 1))
            group_df = group_df.sort_values('정렬순서')
            
            for col, (_, member) in enumerate(group_df.iterrows(), start=1):
                name = str(member.get('이름', ''))
                분류 = member.get('분류결과', '')
                
                # 이름 + 정보 표시 (리더는 별표 추가)
                display_text = name
                if 분류 == '리더':
                    display_text = f"⭐ {name}"
                
                item = QTableWidgetItem(display_text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # 분류에 따른 색상: 리더(초록), 일반(무색), 케어 대상(분홍)
                if 분류 == '리더':
                    item.setBackground(QColor('#d4edda'))  # 초록
                elif 분류 == '케어 대상':
                    item.setBackground(QColor('#f8d7da'))  # 분홍
                # 일반은 배경색 없음
                
                # 툴팁에 상세 정보
                나이 = member.get('나이', '')
                출석 = member.get('출석현황', '')
                출석등급 = member.get('출석등급', '')
                item.setToolTip(f"이름: {name}\n나이: {나이}\n출석: {출석}\n등급: {출석등급}\n분류: {분류}")
                
                table.setItem(row, col, item)
        
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
    
    def populate_table(self, table: QTableWidget, df):
        """DataFrame을 QTableWidget에 표시 (기본 형식)"""
        table.clear()
        table.setRowCount(len(df))
        table.setColumnCount(len(df.columns))
        table.setHorizontalHeaderLabels(df.columns.tolist())
        
        for i, row in df.iterrows():
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # 분류결과에 따른 색상: 리더(초록), 일반(무색), 케어 대상(분홍)
                if df.columns[j] == '분류결과':
                    if value == '리더':
                        item.setBackground(QColor('#d4edda'))
                        item.setForeground(QColor('black'))
                    elif value == '케어 대상':
                        item.setBackground(QColor('#f8d7da'))
                        item.setForeground(QColor('black'))
                    # 일반은 배경색 없음
                
                table.setItem(i, j, item)
        
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    
    def save_result(self):
        """결과 저장"""
        if self.result_df is None:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "결과 저장",
            "sorted_result.xlsx",
            "Excel Files (*.xlsx)"
        )
        
        if file_path:
            try:
                loader = DataLoader()
                # 제약조건도 함께 저장할지 여부
                loader.save_result(
                    self.result_df, 
                    file_path, 
                    self.stats_df,
                    self.constraints_tab.constraint_manager
                )
                self.statusbar.showMessage(f"💾 저장 완료: {file_path}")
                QMessageBox.information(self, "저장 완료", f"결과가 저장되었습니다:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "저장 오류", str(e))


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 폰트 설정
    font = app.font()
    font.setFamily("맑은 고딕")
    font.setPointSize(10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
