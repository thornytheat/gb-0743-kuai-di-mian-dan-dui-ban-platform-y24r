# 快递面单数据字典

## 输入

所有时间需包含时区偏移，接口统一为 UTC，页面以北京时间显示。编号一律为字符串。输入 JSONL 限 256 KiB、2000 个物理行，支持 UTF-8、UTF-8 BOM 和 GB18030。坏行和空白行保留源行与原值，输入末尾的换行是行结束符。出单编号重复时，业务字段归一后相同则保留首行；有矛盾则隔离整组。

| 文件 | 字段 | 说明 |
|---|---|---|
| `sample_data/prints.jsonl` | `label`、`parcel`、`at`、`format`、`device` | 面单、包裹、打印时点、模板族、设备号 |
| 同上 | `dpi`、`rotation`、`origin`、`unit` | 单一 DPI 值 72–1200，支持带 `dpi` 后缀及全角数字。顺时针旋转 0、90、180、270 度。原点 `TL` 左上或 `BL` 左下，单位 `px` 或 `mm` |
| 同上 | `fields` | 必须含 `barcode`、`route`、`recipient`。每项含字符串 `value` 和矩形 `box` |
| 同上 | `replaces` | 可空。重打时填作废旧单编号 |
| `sample_data/templates.jsonl` | `format`、`revision`、`start`、`end` | 同模板族按 `[start,end)` 选最高有效修订号。同修订重叠记录均隔离 |
| 同上 | `paper`、`quiet_mm`、`zones`、`note` | 纸宽与高、两侧静区宽度、模板字段出版范围、备注 |
| `sample_data/parcels.json` | 包裹键、`tracking`、`route`、`recipient` | 仅清除实读字段外侧空白，再逐字符比对 |
| `sample_data/voids.jsonl` | `id`、`label`、`at`、`reason` | 作废登记键、目标面单、时点与原因。原因 `JAM`、`SMEAR` 或 `LOST` |

## 归一与面积

矩形是 `[x,y,w,h]`。坐标允许负数，宽和高须为正，最多六位小数。像素按 `25.4 / DPI` 换算为毫米。先按旋转后纸张高度处理左下原点的 Y 轴，再逆转设备顺时针旋转。矩形宽高在 90° 与 270° 时互换。几何保留精确有理数，输出矩形显示到六位小数。

相交面积为两轴重叠长度之积。边缘接触面积为零。条码沿归一纸面 X 轴向左右各扩一条同高静区，分别计算越过纸张和被其他字段占用的面积。出版范围按字段定义；同一矩形可同时触发多种几何原因。`area_mm2` 是显示值，`area_exact_mm2` 是用于复核的精确分数或整数字符串。

## 作废与重打

以打印和作废发生时点顺序处理。相同时点先作废已存在的旧单，再按面单键排序处理打印。有效面单被成功作废后才能接续重打，重打时点不能早于作废。旧单必须是同一包裹最近一次成功出单记录，且无后继。新单仍接受模板、几何、条码对读的完整检验。已撤销面单保留自身和后继单号，旧批次按原始输入独立复算。

## 写入与导出

| 写入入口 | 参数 |
|---|---|
| `POST /api/intake` | `multipart/form-data` 的 `expected` 和 `prints` |
| `POST /api/tickets/void` | JSON 的 `expected`、`label`、`at`、`reason` |
| `POST /api/tickets/reprint` | JSON 的 `expected`、`target`、`label`、`at`。沿用旧单字段几何，按新时点匹配模板 |
| `POST /api/runs/rerun` | JSON 的 `expected` |
| `POST /api/runs/restore` | JSON 的 `expected`、`target` |

`expected` 为当前完整批次编号。七阶段 API 用 `?run=<编号>` 读取任一已归档批次。批次编号由规则版本、原始输入字节数和 SHA-256 计算。同样内容只归档一次，重跑校验业务证据且保留首次时间和耗时。证据包的 `sha256` 针对外层 `evidence` 对象，计算前按键名排序，序列化为紧凑 UTF-8 JSON，保留中文原字符。
