// env_utils.ts
// this utility will check a student's setup to verify it has
// packages installed, Node/pnpm available, and API keys set
// it references package.json and .env.example for requirements

// ========== NODE.JS BUILT-INS ONLY (no external dependencies) ==========
import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

type Version = [number, number, number];

function parseVersion(raw: string): Version | null {
  const match = raw.replace(/^v/, "").match(/^(\d+)\.(\d+)\.(\d+)/);
  if (!match) return null;
  return [Number(match[1]), Number(match[2]), Number(match[3])];
}

function compareVersions(a: Version, b: Version): number {
  for (let i = 0; i < 3; i++) {
    if (a[i] !== b[i]) return a[i] - b[i];
  }
  return 0;
}

/**
 * Very small subset of npm range checking (^, ~, >=, exact, latest/*).
 * Good enough for a diagnostics script — not a full semver implementation.
 */
function satisfiesSpec(installed: string, spec: string): "ok" | "mismatch" | "unknown" {
  const trimmed = spec.trim();
  if (trimmed === "latest" || trimmed === "*" || trimmed === "") return "ok";

  const installedVersion = parseVersion(installed);
  if (!installedVersion) return "unknown";

  const caret = trimmed.match(/^\^(\d+\.\d+\.\d+)/);
  if (caret) {
    const required = parseVersion(caret[1])!;
    if (installedVersion[0] !== required[0]) return "mismatch";
    return compareVersions(installedVersion, required) >= 0 ? "ok" : "mismatch";
  }

  const tilde = trimmed.match(/^~(\d+\.\d+\.\d+)/);
  if (tilde) {
    const required = parseVersion(tilde[1])!;
    if (installedVersion[0] !== required[0] || installedVersion[1] !== required[1]) return "mismatch";
    return compareVersions(installedVersion, required) >= 0 ? "ok" : "mismatch";
  }

  const gte = trimmed.match(/^>=(\d+\.\d+\.\d+)/);
  if (gte) {
    const required = parseVersion(gte[1])!;
    return compareVersions(installedVersion, required) >= 0 ? "ok" : "mismatch";
  }

  const exact = parseVersion(trimmed);
  if (exact) {
    return compareVersions(installedVersion, exact) === 0 ? "ok" : "mismatch";
  }

  return "unknown";
}

// ========== EARLY NODE ENVIRONMENT DIAGNOSTICS ==========
function checkNodeExecutableAndVersion(): { ok: boolean; issues: string[] } {
  const issues: string[] = [];
  const nodeVersion = process.version;
  const parsed = parseVersion(nodeVersion)!;

  console.log("=".repeat(70));
  console.log("NODE ENVIRONMENT DIAGNOSTICS");
  console.log("=".repeat(70));
  console.log(`Node executable: ${process.execPath}`);
  console.log(`Node version: ${nodeVersion}`);
  console.log(`Platform: ${process.platform}`);
  console.log();

  if (parsed[0] < 20) {
    issues.push(`⚠️  Node ${nodeVersion} is below the minimum required version 20.0.0`);
  } else {
    console.log(`✅ Node version ${nodeVersion} satisfies the minimum required version (>=20.0.0)`);
  }

  const nodeModulesPath = path.join(process.cwd(), "node_modules");
  if (!existsSync(nodeModulesPath)) {
    issues.push("⚠️  node_modules/ not found — dependencies are not installed");
    issues.push("   Run: pnpm install");
  } else {
    console.log(`✅ Dependencies installed at ${nodeModulesPath}`);
  }

  if (issues.length) {
    console.log("\n" + "!".repeat(70));
    console.log("POTENTIAL ISSUES DETECTED:");
    console.log("!".repeat(70));
    issues.forEach((issue) => console.log(issue));
    console.log("\nRECOMMENDATION:");
    console.log("  Run: pnpm install");
    console.log("  Then: pnpm tsx env_utils.ts");
    console.log("!".repeat(70));
  }

  console.log();
  return { ok: issues.length === 0, issues };
}

function checkPackageManager(): void {
  const issues: string[] = [];
  try {
    const version = execFileSync("pnpm", ["--version"], { encoding: "utf8" }).trim();
    console.log(`✅ pnpm is available (v${version})`);
  } catch {
    issues.push("ℹ️  'pnpm' command not found in PATH — this project uses pnpm for package management");
    issues.push("   Install: corepack enable && corepack prepare pnpm@latest --activate");
  }

  if (issues.length) {
    console.log("Package Manager Check:");
    issues.forEach((issue) => console.log(issue));
  }
  console.log();
}

function checkManualInstalls(filePath: string): void {
  if (!existsSync(filePath)) return;

  let manualInstalls: string[] = [];
  const lines = readFileSync(filePath, "utf8").split("\n");
  for (const line of lines) {
    const stripped = line.trim();
    if (stripped.startsWith("# Manual installs for checking:")) {
      const appsStr = stripped.split(":").slice(1).join(":").trim();
      if (appsStr) manualInstalls = appsStr.split(",").map((app) => app.trim());
      break;
    }
  }
  if (!manualInstalls.length) return;

  console.log("Manual Installs Check:");
  const whichCmd = process.platform === "win32" ? "where" : "which";
  for (const app of manualInstalls) {
    try {
      execFileSync(whichCmd, [app], { stdio: "ignore" });
      console.log(`✅ ${app}`);
    } catch {
      console.log(`⚠️  ${app} not found in PATH`);
    }
  }
  console.log();
}

function parseEnvFile(filePath: string): Record<string, string> {
  const values: Record<string, string> = {};
  if (!existsSync(filePath)) return values;

  const lines = readFileSync(filePath, "utf8").split("\n");
  for (const line of lines) {
    const stripped = line.trim();
    if (!stripped || stripped.startsWith("#") || !stripped.includes("=")) continue;

    const idx = stripped.indexOf("=");
    const key = stripped.slice(0, idx).trim();
    let value = stripped.slice(idx + 1).trim();
    if ((value.startsWith("'") && value.endsWith("'")) || (value.startsWith('"') && value.endsWith('"'))) {
      value = value.slice(1, -1);
    }
    values[key] = value;
  }
  return values;
}

/** Return masked form for API keys, or the full value for non-API keys. */
function summarizeValue(key: string, value: string, exampleValue?: string): string {
  const lower = value.toLowerCase();
  if (lower === "true" || lower === "false") return lower;

  const isApiKey = key.endsWith("API_KEY");
  if (!isApiKey) return value;

  // Show the full value if it still matches the placeholder (needs changing).
  if (exampleValue !== undefined && value === exampleValue) return value;

  return value.length > 4 ? `****${value.slice(-4)}` : `****${value}`;
}

function doublecheckEnv(examplePath: string, envPath: string): void {
  if (!existsSync(examplePath)) {
    console.log(`Did not find file ${examplePath}.`);
    console.log("This is used to double check the key settings for the lessons.");
    console.log("This is just a check and is not required.\n");
    return;
  }

  const exampleLines = readFileSync(examplePath, "utf8").split("\n");
  const allExampleValues: Record<string, string> = {};
  const requiredKeys: Record<string, string> = {};
  let isRequiredSection = false;

  for (const line of exampleLines) {
    const stripped = line.trim();
    if (stripped.startsWith("#")) {
      isRequiredSection = stripped.toLowerCase().includes("required");
      continue;
    }
    if (stripped.includes("=")) {
      const idx = stripped.indexOf("=");
      const key = stripped.slice(0, idx).trim();
      let value = stripped.slice(idx + 1).trim();
      if ((value.startsWith("'") && value.endsWith("'")) || (value.startsWith('"') && value.endsWith('"'))) {
        value = value.slice(1, -1);
      }
      allExampleValues[key] = value;
      if (isRequiredSection) requiredKeys[key] = value;
    }
  }

  // `dotenv/config` (used by the lesson scripts) does not override variables
  // already present in the shell environment, so mirror that precedence here.
  const envFileValues = parseEnvFile(envPath);
  const issues: string[] = [];

  console.log("Environment Variables:");
  for (const key of Object.keys(allExampleValues)) {
    const current = process.env[key] ?? envFileValues[key];
    const exampleVal = allExampleValues[key];

    if (current !== undefined && current !== "") {
      console.log(`${key}=${summarizeValue(key, current, exampleVal)}`);
      if (key in requiredKeys && current === exampleVal) {
        issues.push(`  ⚠️  ${key} still has the example/placeholder value`);
      }
    } else {
      console.log(`${key}=<not set>`);
      if (key in requiredKeys) {
        issues.push(`  ⚠️  ${key} is required but not set`);
      }
    }
  }

  const langsmithTracing = (process.env.LANGSMITH_TRACING ?? envFileValues.LANGSMITH_TRACING ?? "").toLowerCase();
  const langsmithApiKey = process.env.LANGSMITH_API_KEY ?? envFileValues.LANGSMITH_API_KEY ?? "";
  const langsmithExample = allExampleValues.LANGSMITH_API_KEY ?? "";

  if (langsmithTracing === "true") {
    if (!langsmithApiKey) {
      issues.push("  ⚠️  LANGSMITH_TRACING is enabled but LANGSMITH_API_KEY is not set");
    } else if (langsmithApiKey === langsmithExample) {
      issues.push(
        "  ⚠️  LANGSMITH_TRACING is enabled but LANGSMITH_API_KEY still has the example/placeholder value"
      );
    } else {
      console.log("\n✅ LANGSMITH_TRACING is enabled and the LANGSMITH_API_KEY is set");
    }
  } else if (langsmithApiKey && langsmithApiKey !== langsmithExample) {
    issues.push("⚠️  LANGSMITH_API_KEY is set, but LANGSMITH_TRACING is disabled");
  }

  if (issues.length) {
    console.log("\nIssues found:");
    issues.forEach((issue) => console.log(issue));
  }
  console.log();
}

// ========== utility to check packages and Node version based on package.json ==========

function fmtRow(cols: string[], widths: number[]): string {
  return cols.map((col, i) => col.padEnd(widths[i])).join(" | ");
}

function doublecheckPkgs(packageJsonPath = "package.json", verbose = false): void {
  if (!existsSync(packageJsonPath)) {
    console.log(`ERROR: ${packageJsonPath} not found.`);
    return;
  }

  const pkg = JSON.parse(readFileSync(packageJsonPath, "utf8"));
  const requiredNodeSpec: string = pkg.engines?.node ?? ">=20.0.0";
  const nodeVersion = process.version.replace(/^v/, "");
  const nodeOk = satisfiesSpec(nodeVersion, requiredNodeSpec) !== "mismatch";

  const deps: Record<string, string> = { ...pkg.dependencies, ...pkg.devDependencies };
  const names = Object.keys(deps);
  if (!names.length) {
    if (verbose || !nodeOk) {
      console.log("No dependencies found in package.json.");
      console.log(`Node ${nodeVersion} ${nodeOk ? "satisfies" : "DOES NOT satisfy"} engines.node: ${requiredNodeSpec}`);
      console.log(`Executable: ${process.execPath}`);
    }
    return;
  }

  const rows: string[][] = [];
  const problems: string[][] = [];

  for (const name of names) {
    const spec = deps[name];
    const depPackageJsonPath = path.join("node_modules", name, "package.json");

    let installed = "-";
    let status = "❌ Missing";

    if (existsSync(depPackageJsonPath)) {
      try {
        const installedPkg = JSON.parse(readFileSync(depPackageJsonPath, "utf8"));
        installed = installedPkg.version ?? "unknown";
        const result = satisfiesSpec(installed, spec);
        status = result === "mismatch" ? "⚠️ Version mismatch" : "✅ OK";
      } catch {
        status = "⚠️ Unreadable";
      }
    }

    const row = [name, spec, installed, status];
    rows.push(row);
    if (!status.startsWith("✅")) problems.push(row);
  }

  const shouldPrint = verbose || !nodeOk || problems.length > 0;
  if (shouldPrint) {
    console.log(`Node ${nodeVersion} ${nodeOk ? "satisfies" : "DOES NOT satisfy"} engines.node: ${requiredNodeSpec}`);

    const headers = ["package", "required", "installed", "status"];
    const widths = headers.map((h, i) => Math.max(h.length, ...rows.map((row) => row[i].length)));
    console.log(fmtRow(headers, widths));
    console.log(fmtRow(widths.map((w) => "-".repeat(w)), widths));
    for (const row of rows) console.log(fmtRow(row, widths));

    if (problems.length) {
      console.log("\nIssues detected:");
      for (const [name, spec, installed, status] of problems) {
        console.log(`- ${name}: ${status} (required ${spec}, installed ${installed})`);
      }
    }

    if (verbose || problems.length || !nodeOk) {
      console.log("\nEnvironment:");
      console.log(`- Executable: ${process.execPath}`);
    }
  }
}

checkNodeExecutableAndVersion();
checkPackageManager();
checkManualInstalls(".env.example");
doublecheckEnv(".env.example", ".env");
doublecheckPkgs("package.json", true);
