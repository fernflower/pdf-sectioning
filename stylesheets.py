#!/usr/bin/env python
# -*- coding: utf-8 -*-

GENERAL_STYLESHEET = \
    """
    QMainWindow { background-color: rgb(83, 83, 83);}

    QToolBar { border: 1px solid rgb(58, 56, 56) }
    QMenu::item:!enabled::text { color: rgb(52, 51, 51) }
    QMenuBar::item{ color: rgb(235, 235, 235);
                    background-color: rgb(81, 81, 81)}

    QScrollArea { background-color: rgb(58, 56, 56);
                    border: 1px solid rgb(58, 56, 56) }

    QScrollBar:horizontal, QScrollBar:vertical
    {
        border: 2px solid grey;
        background: gray;
    }
    QScrollBar::add-page, QScrollBar::sub-page
    {
        background: none;
    }

    #toolBar QPushButton:disabled
    { background-color: rgb(81, 81, 81);
      color: rgb(58, 56, 56)
    }

    QListView, QTabWidget, QTabBar, QMenuBar, QMenu, #toolBar QPushButton
    {
        background-color: rgb(81, 81, 81);
        color: rgb(235, 235, 235);
    }
    QListView { font-size: 12px;
                font-family: "Arial"}
    QListView::item:selected { background: rgb(10, 90, 160); }
    QListView::item { color: rgb(230, 230, 230);
                        border-bottom: 0.5px solid rgb(58, 56, 56);
                    }
    QListView::item::icon {
        padding: 7px;
    }

    QTabWidget::pane { border: 1px solid rgb(58, 56, 56); }
    QTabBar::tab {
        background: solid rgb(81,81,81);
        border: 2px solid rgb(45,45,45);
        border-bottom-color: solid rgb(81,81,81);
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
        min-width: 80px;
        padding: 12px;
    }
    QTabBar::tab::!selected {
        border-bottom-color: solid rgb(45,45,45);
        background: solid rgb(56,56,56)
    }

    QTabBar::tab::text { color: rgb(235, 235, 235); }
    QTabBar::tab:!enabled::text { color: rgb(50, 50, 50); }

    #toolBar QSpinBox, #toolBar QComboBox
    { background-color: rgb(58, 56, 56);
      color: rgb(235, 235, 235)
    }

    QParagraphMark::text { color: rgb(0, 0, 0) }

    QComboBox::down-arrow { color: white }

    """

BLACK_LABEL_STYLESHEET = \
    """ QLabel { color: rgb(235, 235, 235);
                 background-color: rgb(81, 81, 81) }
    """

RULER_STYLESHEET = \
    """ QRubberBand
    { color: rgb(0, 0, 0);
      background-color: rgb(200, 0, 0);
      opacity: 50
    }
    """

RULER_SELECTED_STYLESHEET = \
    """ QRubberBand
    { color: rgb(0, 0, 0);
      background-color: rgb(200, 0, 0);
      opacity: 20
    }
    """

LIST_ITEM_DESELECT = \
    """
    QObjectElem, QZone
    {
      color: rgb(120, 120, 120);
    }
    """
