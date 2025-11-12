# FileFlow Frontend

Native macOS desktop application for FileFlow Manager built with Tauri and Svelte.

## Overview

The FileFlow frontend provides a native macOS GUI for file organization with:

- **Tauri framework** for native desktop integration
- **Svelte 4** for reactive UI components
- **TypeScript** for type safety
- **Tailwind CSS + daisyUI** for styling
- **Tauri IPC** for communication with Python backend via Poetry subprocess

## Architecture

```
frontend/
├── src/                          # Svelte application
│   ├── routes/                   # Page components (SvelteKit routing)
│   │   ├── +layout.svelte        # Base layout with navigation
│   │   ├── +page.svelte          # Index/redirect
│   │   ├── App.svelte            # Main app with routing logic
│   │   ├── Dashboard.svelte      # File organization tab
│   │   ├── Rules.svelte          # Rule management tab
│   │   ├── LargeFiles.svelte     # Large file discovery tab
│   │   ├── OldFiles.svelte       # Old file discovery tab
│   │   └── Settings.svelte       # Configuration management tab
│   │
│   ├── lib/                      # Shared code
│   │   ├── components/           # Reusable UI components
│   │   │   ├── ProgressBar.svelte    # Progress indicator
│   │   │   ├── ConfirmDialog.svelte  # Confirmation modal
│   │   │   ├── FileList.svelte       # File display table
│   │   │   ├── RuleEditor.svelte     # Rule create/edit modal
│   │   │   └── ErrorAlert.svelte     # Error message display
│   │   │
│   │   ├── stores/               # Svelte stores (state management)
│   │   │   ├── scan.ts           # Scan state and operations
│   │   │   ├── rules.ts          # Rules state
│   │   │   ├── files.ts          # File lists (large/old)
│   │   │   └── settings.ts       # Configuration state
│   │   │
│   │   ├── api.ts                # Tauri IPC wrapper functions
│   │   └── types.ts              # TypeScript type definitions
│   │
│   ├── app.css                   # Global styles (Tailwind imports)
│   └── app.html                  # HTML template
│
├── src-tauri/                    # Tauri (Rust) bridge
│   ├── src/
│   │   └── main.rs               # Tauri commands + Python backend invocation
│   ├── Cargo.toml                # Rust dependencies
│   ├── tauri.conf.json           # Tauri configuration
│   └── icons/                    # Application icons
│
├── package.json                  # Node.js dependencies
├── vite.config.ts                # Vite build configuration
├── tailwind.config.js            # Tailwind CSS configuration
├── svelte.config.js              # Svelte compiler configuration
└── tsconfig.json                 # TypeScript configuration
```

## Technology Stack

### Frontend Framework

- **Tauri 1.5+** - Native desktop framework (Rust-based)
- **Svelte 4** - Reactive component framework
- **TypeScript 5.0+** - Type-safe JavaScript
- **Vite** - Fast build tool and dev server

### Styling

- **Tailwind CSS 3** - Utility-first CSS framework
- **daisyUI** - Component library for Tailwind
- **PostCSS** - CSS processing

### State Management

- **Svelte Stores** - Built-in reactive state management
- Stores for: scan operations, rules, files, settings

### Development Tools

- **ESLint** - JavaScript/TypeScript linting
- **Prettier** - Code formatting
- **TypeScript Compiler** - Type checking

## Installation

### Prerequisites

- Node.js 18.0+ and pnpm
- Rust 1.70+ (for Tauri)
- Python 3.10+ with Poetry (backend dependency)

### Install Dependencies

```bash
cd frontend
pnpm install
```

This installs:

- Tauri CLI and runtime
- Svelte and SvelteKit
- Tailwind CSS and daisyUI
- TypeScript and build tools

## Development

### Run Development Server

```bash
pnpm tauri dev
```

This starts:

1. Vite dev server on `http://localhost:5173`
2. Tauri window with hot-reload enabled
3. File watcher for automatic recompilation

**Hot Reload**: Edit `.svelte` files and see changes instantly

### Development Tips

**Enable Devtools**:

- Right-click in app → "Inspect Element"
- Or add to `tauri.conf.json`:
  ```json
  {
    "tauri": {
      "windows": [
        {
          "devtools": true
        }
      ]
    }
  }
  ```

**View Logs**:

- Tauri logs: Check terminal running `pnpm tauri dev`
- Backend logs: `~/.local/share/fileflow/fileflow.log`

## User Interface

### 5 Main Tabs

**1. Dashboard** (`Dashboard.svelte`):

- Scan files button (dry-run)
- Execute operations button
- Scan results table with operation details
- Operation history display
- Statistics (files processed, space saved)

**2. Rules** (`Rules.svelte`):

- List of all organization rules
- Enable/disable toggle for each rule
- Create new rule button
- Edit/delete rule actions
- Rule priority sorting
- Rule editor modal (`RuleEditor.svelte`)

**3. Large Files** (`LargeFiles.svelte`):

- Threshold slider (default 100MB)
- Scan button to discover large files
- File list with size, path, modification date
- Filter by location
- Batch select and delete
- Space to be freed estimate

**4. Old Files** (`OldFiles.svelte`):

- Age threshold slider (default 90 days)
- Scan button to discover old files
- File list with age, path, size
- Filter by file type
- Batch select and delete
- Confirmation before deletion

**5. Settings** (`Settings.svelte`):

- Current configuration display
- Export configuration button
- Import configuration button (replace or merge)
- Configuration validation
- Environment variable preview

### Reusable Components

**ProgressBar** (`ProgressBar.svelte`):

```svelte
<ProgressBar current={processed} total={totalFiles} label="Processing files..." />
```

**ConfirmDialog** (`ConfirmDialog.svelte`):

```svelte
<ConfirmDialog
  isOpen={showConfirm}
  title="Delete Files"
  message="Are you sure you want to delete 10 files?"
  onConfirm={handleDelete}
  onCancel={() => (showConfirm = false)}
/>
```

**FileList** (`FileList.svelte`):

```svelte
<FileList files={largeFiles} columns={["name", "size", "path"]} onSelect={handleSelect} />
```

## State Management

### Svelte Stores

**scan.ts** - Scan state:

```typescript
export const scanState = writable({
  isScanning: false,
  results: [],
  operations: [],
  progress: 0,
});

export async function executeScan(dryRun: boolean) {
  scanState.update((s) => ({ ...s, isScanning: true }));
  const results = await scanFiles(dryRun);
  scanState.update((s) => ({ ...s, results, isScanning: false }));
}
```

**rules.ts** - Rules state:

```typescript
export const rulesState = writable<Rule[]>([]);

export async function loadRules() {
  const rules = await getRules();
  rulesState.set(rules);
}

export async function toggleRule(id: string, enabled: boolean) {
  if (enabled) {
    await enableRule(id);
  } else {
    await disableRule(id);
  }
  await loadRules();
}
```

**files.ts** - File lists:

```typescript
export const largeFilesState = writable<FileInfo[]>([]);
export const oldFilesState = writable<FileInfo[]>([]);

export async function scanLargeFiles(thresholdMB: number) {
  const files = await findLargeFiles(thresholdMB);
  largeFilesState.set(files);
}
```

**settings.ts** - Configuration:

```typescript
export const configState = writable<Configuration | null>(null);

export async function loadConfiguration() {
  const config = await getConfiguration();
  configState.set(config);
}

export async function exportConfig(path: string) {
  await exportConfiguration(path);
}
```

## API Integration

### Tauri IPC Communication

**api.ts** - Wrapper functions for Tauri commands:

```typescript
import { invoke } from "@tauri-apps/api/tauri";

// Scan operations
export async function scanFiles(dryRun: boolean) {
  return await invoke("scan_files", { dryRun });
}

export async function executeOperations(operations: Operation[]) {
  return await invoke("execute_operations", { operations });
}

// Rule management
export async function getRules() {
  return await invoke("get_rules", {});
}

export async function createRule(rule: Rule) {
  return await invoke("create_rule", { rule });
}

export async function updateRule(id: string, updates: Partial<Rule>) {
  return await invoke("update_rule", { id, updates });
}

export async function deleteRule(id: string) {
  return await invoke("delete_rule", { id });
}

// File discovery
export async function findLargeFiles(thresholdMB: number) {
  return await invoke("find_large_files", { thresholdMb: thresholdMB });
}

export async function findOldFiles(thresholdDays: number) {
  return await invoke("find_old_files", { thresholdDays });
}

// Configuration
export async function getConfiguration() {
  return await invoke("get_configuration", {});
}

export async function exportConfiguration(path: string) {
  return await invoke("export_configuration", { destinationPath: path });
}

export async function importConfiguration(path: string, merge: boolean) {
  return await invoke("import_configuration", { sourcePath: path, merge });
}
```

### Tauri Rust Bridge

**src-tauri/src/main.rs** - Rust commands that invoke Python backend:

```rust
#[tauri::command]
async fn scan_files(dry_run: bool) -> Result<serde_json::Value, String> {
    // Find Poetry and backend directory
    let backend_dir = /* path to ../backend */;

    // Execute Python command via Poetry
    let output = Command::new("poetry")
        .current_dir(&backend_dir)
        .arg("run").arg("python").arg("-m")
        .arg("fileflow_api.tauri_commands")
        .arg("scan_files")
        .arg(serde_json::to_string(&json!({ "dry_run": dry_run }))?)
        .output()
        .map_err(|e| format!("Failed to execute: {}", e))?;

    // Parse JSON response
    let stdout = String::from_utf8_lossy(&output.stdout);
    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse: {}", e))
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            scan_files,
            execute_operations,
            get_rules,
            create_rule,
            update_rule,
            delete_rule,
            enable_rule,
            disable_rule,
            find_large_files,
            find_old_files,
            delete_files,
            get_operation_history,
            get_configuration,
            export_configuration,
            import_configuration
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

## Building for Production

### Development Build

```bash
pnpm tauri build
```

This creates:

- **DMG installer**: `src-tauri/target/release/bundle/dmg/FileFlow Manager_0.1.0_aarch64.dmg` (Apple Silicon)
- **DMG installer**: `src-tauri/target/release/bundle/dmg/FileFlow Manager_0.1.0_x64.dmg` (Intel)
- **App bundle**: `src-tauri/target/release/bundle/macos/FileFlow Manager.app`

### Build Configuration

**tauri.conf.json** - Main configuration:

```json
{
  "package": {
    "productName": "FileFlow Manager",
    "version": "0.9.0"
  },
  "build": {
    "beforeDevCommand": "pnpm dev",
    "beforeBuildCommand": "pnpm build",
    "devPath": "http://localhost:5173",
    "distDir": "../build"
  },
  "tauri": {
    "bundle": {
      "active": true,
      "targets": ["dmg", "app"],
      "identifier": "com.fileflow.manager",
      "icon": ["icons/32x32.png", "icons/128x128.png", "icons/icon.icns"]
    },
    "windows": [
      {
        "title": "FileFlow Manager",
        "width": 1200,
        "height": 800,
        "resizable": true,
        "fullscreen": false
      }
    ],
    "security": {
      "csp": null
    },
    "allowlist": {
      "all": false,
      "dialog": {
        "all": true,
        "open": true,
        "save": true
      },
      "fs": {
        "all": true,
        "readFile": true,
        "writeFile": true,
        "scope": ["$HOME/**"]
      }
    }
  }
}
```

### Code Signing (for Distribution)

To distribute outside the App Store, you need to sign the app:

```bash
# Sign with Apple Developer ID
codesign --deep --force --sign "Developer ID Application: Your Name (TEAM_ID)" "src-tauri/target/release/bundle/macos/FileFlow Manager.app"

# Notarize with Apple
xcrun notarytool submit "src-tauri/target/release/bundle/dmg/FileFlow Manager_0.9.0_aarch64.dmg" --apple-id "your@email.com" --password "app-specific-password" --team-id "TEAM_ID"
```

## Code Quality

### Linting

```bash
# Lint TypeScript and Svelte
pnpm eslint .

# Auto-fix issues
pnpm eslint . --fix
```

### Formatting

```bash
# Format with Prettier
pnpm prettier --write .
```

### Type Checking

```bash
# Run TypeScript compiler
pnpm tsc --noEmit
```

## Styling

### Tailwind CSS

Global styles in `app.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom utilities */
@layer utilities {
  .truncate-path {
    @apply truncate max-w-xs;
  }
}
```

### daisyUI Components

Pre-built components from daisyUI:

```svelte
<button class="btn btn-primary">Primary Button</button>
<div class="card bg-base-100 shadow-xl">
  <div class="card-body">
    <h2 class="card-title">Card Title</h2>
    <p>Card content</p>
  </div>
</div>
```

**Theme Configuration** (`tailwind.config.js`):

```javascript
module.exports = {
  content: ["./src/**/*.{html,js,svelte,ts}"],
  theme: {
    extend: {},
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: ["light", "dark"],
  },
};
```

## Troubleshooting

### Common Issues

**Issue**: `Failed to execute Python backend`
**Solution**: Ensure Poetry is installed and backend dependencies are installed (`cd backend && poetry install`)

**Issue**: Tauri dev server won't start
**Solution**: Check if port 5173 is available. Kill any process using it: `lsof -ti:5173 | xargs kill`

**Issue**: Hot reload not working
**Solution**: Restart dev server. Check file permissions. Ensure Vite config is correct.

**Issue**: TypeScript errors in IDE
**Solution**: Restart TypeScript language server. Run `pnpm tsc --noEmit` to check errors.

**Issue**: App bundle won't run on other Macs
**Solution**: Sign and notarize the app with Apple Developer ID.

### Debug Mode

**Enable verbose logging**:

```bash
RUST_LOG=debug pnpm tauri dev
```

**Check Tauri logs**:

- Look for errors in terminal output
- Check backend logs: `~/.local/share/fileflow/fileflow.log`

## Testing

### Component Testing (TODO - Phase 8)

```bash
# Run Vitest tests
pnpm test

# Run with coverage
pnpm test --coverage
```

### Integration Testing (TODO - Phase 8)

Test Tauri IPC communication:

```typescript
import { test, expect } from "vitest";
import { scanFiles } from "./api";

test("scanFiles returns results", async () => {
  const results = await scanFiles(true);
  expect(results).toBeDefined();
  expect(Array.isArray(results)).toBe(true);
});
```

## Contributing

When contributing to the frontend:

1. **Follow TypeScript conventions** - Use strict typing, avoid `any`
2. **Write component documentation** - Add JSDoc comments
3. **Use Svelte best practices** - Reactive statements, proper lifecycle
4. **Test UI manually** - Verify all user flows work
5. **Update this README** if adding new pages/components

## Resources

- **Tauri Documentation**: https://tauri.app/
- **Svelte Documentation**: https://svelte.dev/
- **Tailwind CSS**: https://tailwindcss.com/
- **daisyUI Components**: https://daisyui.com/

## License

TBD
