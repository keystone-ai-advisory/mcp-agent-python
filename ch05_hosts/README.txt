例だけです。実機の設定ファイルは書き換えていません。<ユーザー名> と版は自分の環境に直す。
Claude Desktop: %APPDATA%\Claude\claude_desktop_config.json に置き、完全に終了して起動し直す
Claude Code:   claude mcp add --transport http helpdesk http://127.0.0.1:3002/mcp --header "Authorization: Bearer <token>"
VS Code:       .vscode/mcp.json
