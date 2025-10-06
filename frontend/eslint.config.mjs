// ESLint 9 Flat Config for the Next.js + TypeScript project
// Migration reference: https://eslint.org/docs/latest/use/migrate-to-9.0.0#flat-config

import { defineConfig, globalIgnores } from 'eslint/config';
import js from '@eslint/js';
import tsParser from '@typescript-eslint/parser';
import typescriptEslint from '@typescript-eslint/eslint-plugin';
import { FlatCompat } from '@eslint/eslintrc';
import reactPlugin from 'eslint-plugin-react';
import reactHooksPlugin from 'eslint-plugin-react-hooks';
import importPlugin from 'eslint-plugin-import';
import nextPlugin from '@next/eslint-plugin-next';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// Needed so FlatCompat can resolve legacy shareable configs like "next/core-web-vitals"
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const compat = new FlatCompat({ baseDirectory: __dirname });

export default defineConfig([
    // Global ignores (applied before any configs)
    globalIgnores([
        '.next/**',
        'node_modules/**',
        'dist/**',
        'coverage/**',
        'next-env.d.ts',
        'postcss.config.js',
        'tailwind.config.js',
        'next.config.js',
        '.eslintrc.*'
    ]),

    // Base JS recommended rules
    js.configs.recommended,

    // Convert legacy Next + TypeScript recommended configs
    ...compat.extends('next/core-web-vitals', 'plugin:@typescript-eslint/recommended'),

    // Our project specific config
    {
        files: ['**/*.{js,jsx,ts,tsx}'],
        languageOptions: {
            parser: tsParser,
            ecmaVersion: 2022,
            sourceType: 'module',
        },
        plugins: {
            '@typescript-eslint': typescriptEslint,
            react: reactPlugin,
            'react-hooks': reactHooksPlugin,
            import: importPlugin,
            '@next/next': nextPlugin,
        },
        settings: {
            react: { version: 'detect' },
        },
        rules: {
            // Align with previous legacy config customizations
            '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
            'react/react-in-jsx-scope': 'off',
            // Temporary migration softening (can be tightened later)
            '@typescript-eslint/no-explicit-any': 'warn',
            '@typescript-eslint/no-require-imports': 'off',

            // Helpful additional defaults (adjust as desired)
            'react-hooks/rules-of-hooks': 'error',
            'react-hooks/exhaustive-deps': 'warn',
            'import/order': ['warn', { groups: ['builtin', 'external', 'internal', 'parent', 'sibling', 'index'], 'newlines-between': 'always' }],
            'import/no-unresolved': 'off', // Next.js / TS handles this
            '@typescript-eslint/no-unnecessary-type-constraint': 'off', // temp during migration
            // Enforce consistent member ordering within import statements.
            // Let import/order handle grouping; ignoreDeclarationSort avoids conflict.
            'sort-imports': ['warn', {
                ignoreCase: true,
                ignoreDeclarationSort: true, // defer module-level ordering to import/order
                ignoreMemberSort: false,
                memberSyntaxSortOrder: ['none', 'all', 'multiple', 'single'],
                allowSeparatedGroups: true,
            }],
            // Enforce 4-space indentation (aligns with editor.tabSize for TS)
            indent: ['error', 4, {
                SwitchCase: 1,
                VariableDeclarator: 1,
                ImportDeclaration: 1,
                flatTernaryExpressions: false,
                offsetTernaryExpressions: false,
                ignoreComments: false,
            }],
        }
    },
]);