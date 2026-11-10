import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    files: ["**/*.{ts,tsx,mts,cts}"],
    rules: {
      // A leading underscore marks a parameter deliberately retained for a
      // callback or interface signature. Rest siblings intentionally omit
      // properties from the copy. Other unused locals still report normally.
      "@typescript-eslint/no-unused-vars": ["warn", {
        argsIgnorePattern: "^_",
        ignoreRestSiblings: true,
      }],
    },
  },
  {
    // These snippets are read as inputs by the corresponding governance scanner.
    // Their declarations are intentionally never invoked by the TypeScript runtime.
    files: [
      "scripts/governance/dualoutput_toolname_fixtures/**/*.ts",
      "scripts/governance/fact_category_pin_fixtures/**/*.ts",
      "scripts/governance/no_raw_token_narrative_fixtures/**/*.ts",
    ],
    rules: { "@typescript-eslint/no-unused-vars": "off" },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
