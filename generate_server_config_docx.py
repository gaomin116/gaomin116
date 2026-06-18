#!/usr/bin/env python3
"""Generate hardware environment configuration table as .docx."""

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


def set_cell_font(cell, text, bold=False, size=10.5):
    cell.text = ""
    paragraph = cell.paragraphs[0]
    run = paragraph.add_run(text)
    run.font.name = "宋体"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.size = Pt(size)
    run.bold = bold


def main():
    output_path = "/workspace/表1硬件环境配置表.docx"

    doc = Document()

    # Page margins
    section = doc.sections[0]
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(2.54)
    section.right_margin = Cm(2.54)

    # Title
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("表1  硬件环境配置表")
    run.bold = True
    run.font.name = "黑体"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
    run.font.size = Pt(14)

    doc.add_paragraph()

    servers = [
        {
            "index": "1",
            "name": "应用服务器（ManBing-app）",
            "config": (
                "（1）设备配置4颗处理器，2.10GHz主频（Intel Xeon Gold 5318Y）；\n"
                "（2）内存配置16GB；\n"
                "（3）硬盘配置2块VMware虚拟SCSI硬盘；\n"
                "（4）网络接口配置1块vmxnet3以太网适配器（VMware虚拟万兆网卡）；\n"
                "（5）Microsoft Windows Server 2019 Standard操作系统（64位）；"
            ),
            "count": "1台",
            "remark": (
                "虚拟机部署于VMware平台；"
                "计算机全名：ManBing-app.hnzyfy.com；"
                "域：hnzyfy.com"
            ),
        },
        {
            "index": "2",
            "name": "应用服务器（ManBing-app-w）",
            "config": (
                "（1）设备配置4颗处理器，2.0GHz主频（Intel Xeon Gold 6330）；\n"
                "（2）内存配置16GB；\n"
                "（3）硬盘配置2块VMware虚拟SCSI硬盘；\n"
                "（4）网络接口配置1块vmxnet3以太网适配器（VMware虚拟万兆网卡）；\n"
                "（5）Microsoft Windows Server 2019 Standard操作系统（64位）；"
            ),
            "count": "1台",
            "remark": (
                "虚拟机部署于VMware平台；"
                "计算机名：ManBing-app-w；"
                "工作组：WORKGROUP"
            ),
        },
    ]

    table = doc.add_table(rows=1, cols=5)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    headers = ["序号", "硬件设备名称", "配置要求", "数量", "备注"]
    widths = [Cm(1.2), Cm(3.5), Cm(8.5), Cm(1.5), Cm(4.0)]

    header_cells = table.rows[0].cells
    for i, header in enumerate(headers):
        set_cell_font(header_cells[i], header, bold=True)
        header_cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        header_cells[i].width = widths[i]

    for server in servers:
        row_cells = table.add_row().cells
        set_cell_font(row_cells[0], server["index"])
        row_cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        set_cell_font(row_cells[1], server["name"])
        row_cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        set_cell_font(row_cells[2], server["config"])
        row_cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT

        set_cell_font(row_cells[3], server["count"])
        row_cells[3].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        set_cell_font(row_cells[4], server["remark"])
        row_cells[4].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT

        for i, width in enumerate(widths):
            row_cells[i].width = width

    doc.save(output_path)
    print(f"Generated: {output_path}")


if __name__ == "__main__":
    main()
