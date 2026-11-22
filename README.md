# 快递面单对版台

仓库打印运维员通过设备出单回执、模板版本和包裹台账复查哪些面单可以发运。工作台把不同设备的字段矩形换算到同一张纸面，标出字段遮挡、静区和越界，提供作废、重打和批次复盘。

## 启动与检查

```bash
docker compose up --build
```

访问 [工作台](http://localhost:18432)。首次启动写入样例，后续使用 `label_data` 命名卷。可通过 `LABEL_DB` 指定另一个 SQLite 文件开启本地演示。

本地使用 Python 3.12。

```bash
python -m pip install -r requirements.txt
python -m flask --app app.main:create_app run --port 18432
python -m pytest -q
```

## 样例复核

1. 在「坐标归一」选 `L-002`。源设备上报 254 DPI、90°、左下原点和像素坐标，归一后条码矩形为 `20, 20, 60, 14` mm。
2. 在「边界遮挡」筛选字段相交，选择 `L-006` 查看纸面热区。条码和路由码相交 7 mm²，路由另占右静区 28 mm²。`L-005` 只有后一个问题。
3. 在「重打工单」查看 `L-001 → L-001-R`。给已作废的 `L-015` 填新面单号 `L-015-NEW`，以 `2026-11-20 08:38:00` 提交，包裹 `0015` 恢复一张可发面单。可打开历史并回切原批次。
4. 「重跑批次」按已归档原始文件重算。「下载证据」保存所选批次的单份 JSON。

## 七个入口

| 页面 | 接口 | 结果 |
|---|---|---|
| 面单收件 | `GET /api/intake`、`POST /api/intake` | 逐行采信、原值保留和隔离 |
| 模板生效 | `GET /api/templates` | 有效版本、隔离项和面单绑定 |
| 坐标归一 | `GET /api/coordinates` | 归一矩形与设备换算依据 |
| 条码字段对读 | `GET /api/barcode` | 实读值与包裹台账差异 |
| 边界遮挡 | `GET /api/occlusion` | 相交、静区、出版范围与纸面边界 |
| 出单勾稽 | `GET /api/reconcile` | 有效、撤销、隔离与逐包裹可发数 |
| 重打工单 | `GET /api/tickets`、`POST /api/tickets/void`、`POST /api/tickets/reprint` | 作废证据、重打链和批次历史 |

设备回执提供字段识读值和矩形，支持替换出单 JSONL。模板和包裹台账随样例提供。版面判断依据轴对齐矩形，未接入真实打印机或扫码设备。

[数据字典与写入格式](docs/DATA-DICTIONARY.md) · [规则和用例索引](docs/DEPTH.md)
