# 快递面单对版台规则与测试索引

- 规模为中型，面向仓库打印运维员。
- 按出单时点裁决模板，将矩形按 DPI、旋转和原点归一，保留面积和静区证据。同一包裹的下一张有效面单必须接续已作废面单。

## 功能模块

| 模块 | 使用者动作 | 入口 | 核心文件 | 测试 |
|---|---|---|---|---|
| M1 面单收件 | 替换回执，核对重复、冲突和坏行 | `GET /api/intake` `POST /api/intake` | `app/modules/intake/service.py` `app/modules/intake/reader.py` | `tests/test_intake.py` |
| M2 模板生效 | 查看打印时点命中和重叠版本 | `GET /api/templates` | `app/modules/templates/service.py` `app/modules/templates/versions.py` | `tests/test_templates.py` |
| M3 坐标归一 | 核对设备坐标和纸面换算 | `GET /api/coordinates` | `app/modules/coordinates/calibration.py` `app/modules/coordinates/box.py` | `tests/test_coordinates.py` |
| M4 条码字段对读 | 比对运单号、路由码、收件代号 | `GET /api/barcode` | `app/modules/barcode/service.py` | `tests/test_barcode.py` |
| M5 边界遮挡 | 筛选静区、版位和相交面积 | `GET /api/occlusion` | `app/modules/occlusion/rules.py` `app/modules/occlusion/service.py` | `tests/test_occlusion.py` |
| M6 出单勾稽 | 清点输入、结果与包裹可发资格 | `GET /api/reconcile` | `app/modules/reconcile/service.py` | `tests/test_reconcile.py` |
| M7 重打工单 | 作废、重打、复算与回切旧批次 | `GET /api/tickets` `POST /api/tickets/void` `POST /api/tickets/reprint` `GET /api/runs/<run_id>/evidence.json` | `app/modules/tickets/ledger.py` `app/modules/tickets/service.py` `app/store.py` | `tests/test_tickets.py` |

## 陷阱登记

| TRAP | 现象 | 朴素实现会怎样 | 本项目处理 | 处理位置 | 测试 |
|---|---|---|---|---|---|
| TRAP-01 | 中文设备回执使用 GB18030 | UTF-8 解码失败 | 测试以带中文样例回执检验回退编码 | `app/modules/intake/reader.py` | `tests/test_intake.py::test_gb18030_crlf_and_lf_preserve_records` |
| TRAP-02 | `prints.jsonl` 有 BOM | 第一条合法行误隔离 | 先剥离 BOM | `app/modules/intake/reader.py` | `tests/test_intake.py::test_bom_and_leading_zero_packaging` |
| TRAP-03 | 拼接回执混用 LF、CRLF | 物理行号有偏差 | 只在换行处拆行，移除末尾 CR | `app/modules/intake/reader.py` | `tests/test_intake.py::test_gb18030_crlf_and_lf_preserve_records` |
| TRAP-06 | `L-002` DPI 含全角数字和单位 | 无法识别设备 DPI | NFKC 归一并验证唯一数值 | `app/modules/coordinates/calibration.py` | `tests/test_coordinates.py::test_fullwidth_dpi_90_degree_lower_left_px_matches_upper_left_mm` |
| TRAP-08 | `prints.jsonl` 有前导零包裹编号 | 转数值后与台账失配 | 包裹号、条码值均保留字符串 | `app/modules/intake/contract.py` | `tests/test_intake.py::test_bom_and_leading_zero_packaging` |
| TRAP-13 | `L-001-R` 在文件靠后、发生时点靠前 | 工单顺序错位 | 按发生时点和固定键排序 | `app/modules/intake/service.py` | `tests/test_intake.py::test_late_file_rows_are_sorted_by_actual_time` |
| TRAP-14 | `L-024` 同号不同 DPI | 后一笔覆盖前一笔 | 矛盾回执两条隔离，精确重复保留首行 | `app/modules/intake/service.py` | `tests/test_intake.py::test_conflicting_repeats_quarantine_both_and_identical_retries_keep_one` |
| TRAP-15 | `L-001` 毫米，`L-002` 像素 | 不同设备矩形直接比较 | 以 `25.4 / DPI` 换算后反向去旋转 | `app/modules/coordinates/calibration.py` | `tests/test_coordinates.py::test_fullwidth_dpi_90_degree_lower_left_px_matches_upper_left_mm` |
| TRAP-16 | `prints.jsonl` 第 37 行未写完 | 记录消失或整批失败 | 坏行连原值隔离 | `app/modules/intake/reader.py` | `tests/test_intake.py::test_truncated_last_payload_is_isolated_with_exact_raw` |
| TRAP-19 | `prints.jsonl` 第 38 行有两个面单键 | JSON 解析器默认取后者 | 按重复字段原因隔离 | `app/modules/intake/reader.py` | `tests/test_intake.py::test_duplicate_json_key_does_not_silently_overwrite` |
| TRAP-23 | `L-019`、`L-021` 卡在版本起止点 | 双绑定或不绑定 | 区间左闭右开 | `app/modules/templates/service.py` | `tests/test_templates.py::test_half_open_boundaries_choose_new_revision_then_fall_back` |
| TRAP-25 | `templates.jsonl` 两条修订 3 重叠 | 选择任意一条 | 冲突版本隔离，剩余取最高修订号 | `app/modules/templates/versions.py` | `tests/test_templates.py::test_same_revision_overlap_is_quarantined_without_losing_older_versions` |
| TRAP-26 | 旧批次页面继续登记作废 | 已发布批次被覆盖 | 事务内核对当前批次编号 | `app/store.py` | `tests/test_tickets.py::test_void_new_version_rejects_stale_write_and_restores_original` |

## 对账规则

- 每条出单输入归入有效、撤销或隔离。空白、坏行、采信重复均计入隔离。
- 包裹最多有一张有效面单；历史作废仍保留前后继和作废登记。作废登记另外勾稽，不计入出单数。
- 面单物理检测与工单资格各保留自己的依据，几何有问题的回执不进入可发链。
