# archive —— 一次性文件归档

这里的东西都**不参与运行**，留着是为了查旧行为、对比 1.0 基线。需要时再取，不要在 `C:\Users\Lenovo\petgame` 根目录直接改它们。

| 文件 | 说明 |
|---|---|
| `pet_web_single_backup.py` | 拆包前的单文件版（233 KB），当 1.0 基线保留 |
| `player_pet.manual_backup.txt` | 早期手动备份档 |
| `player_pet.pre_apptest.txt` | 上 AppTest 之前的档 |
| `player_pet.pre_fx.txt` | 加特效之前的档 |
| `player_pet.pre_goals.txt` | 加周/月目标之前的档 |
| `player_pet.txt.json.bak` | 曾经试过 JSON 方案时的备份（最终仍用纯文本） |
| `player_pet.txt.legacy.bak` | 早期格式的旧档 |

当前正式存档是根目录的 `player_pet.txt`（纯文本，`version = 4`），自动备份在 `save_backups/`。
