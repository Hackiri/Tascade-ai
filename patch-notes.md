# Tascade AI v0.2.5 Release Notes

## Bug Fixes
- Fixed port mismatch issue between CLI and MCP server
- Resolved inconsistency where server announced port 8766 but listened on port 8767
- Improved command-line argument handling in the server

## Enhancements
- Updated documentation to consistently use port 8766
- Added utility scripts for interacting with the MCP server
- Enhanced error handling and logging

## Installation
```bash
npm install -g tascade-ai@0.2.5
```

This patch release fixes an important port mismatch issue with the MCP server that was causing confusion when connecting to the server. The server now properly respects the port specified via command-line arguments and consistently uses port 8766 by default.

## Feedback
We welcome your feedback and contributions! Please report any issues on our [GitHub repository](https://github.com/Hackiri/tascade-ai/issues).
