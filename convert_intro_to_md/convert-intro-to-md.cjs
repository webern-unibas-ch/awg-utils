#!/usr/bin/env node
/*
 * Convert AWG intro JSON (HTML fragments) to Markdown.
 *
 * Usage:
 *   node scripts/convert-intro-to-md.cjs \
 *     src/assets/data/edition/series/1/section/5/intro.json \
 *     src/assets/data/edition/series/1/section/5/intro.md
 *
 * Needs Turndown (yarn add -D turndown) to convert HTML to Markdown.
 */

const fs = require('fs');
const path = require('path');
const TurndownService = require('turndown');

function normalizeWhitespace(text) {
    return text
        .replace(/\u00a0/g, ' ')
        .replace(/\n{3,}/g, '\n\n')
        .trim();
}

/**
 * Remove Angular event bindings like (click)="..." or (click)='...' from HTML.
 */
function stripAngularBindings(html) {
    return html
        .replace(/\s\([^)]+\)="[^"]*"/g, '')
        .replace(/\s\([^)]+\)='[^']*'/g, '');
}

/**
 * Replace <sup><a id='note-ref-N' ...>N</a></sup> with @@FNREF_N@@ tokens so
 * Turndown does not escape or transform them. The caller replaces tokens with
 * [^N] after Turndown has finished.
 */
function replaceFootnoteRefs(html) {
    return html.replace(
        /<sup>\s*<a\b[^>]*\bid=(['"])note-ref-(\d+)\1[^>]*>[\s\S]*?<\/a>\s*<\/sup>/gi,
        (_match, _q, num) => `@@FNREF_${num}@@`
    );
}

/**
 * Parse blockNotes HTML strings into a Map of noteNum -> inner HTML content.
 *
 * Each entry looks like:
 *   <p id='note-N' class='...'>\n     <a class='note-backlink' ...>N</a> | actual text...\n   </p>
 */
function parseBlockNotes(blockNotes) {
    const map = new Map();
    for (const noteHtml of blockNotes) {
        const idMatch = noteHtml.match(/\bid=(['"])note-(\d+)\1/i);
        if (!idMatch) continue;
        const noteNum = idMatch[2];

        const innerHtml = noteHtml
            // Strip the note-backlink anchor and the pipe separator that follows it
            .replace(/<a\b[^>]*class=(['"])[^'"]*note-backlink[^'"]*\1[^>]*>[\s\S]*?<\/a>\s*\|\s*/i, '')
            // Strip wrapping <p ...> and </p>
            .replace(/^<p\b[^>]*>/i, '')
            .replace(/<\/p>\s*$/i, '')
            .trim();

        map.set(noteNum, innerHtml);
    }
    return map;
}

function createTurndown() {
    const td = new TurndownService({
        headingStyle: 'atx',
        codeBlockStyle: 'fenced',
        bulletListMarker: '-',
        emDelimiter: '*',
    });
    // Keep tables as raw HTML to preserve structure and formatting.
    td.keep(['table', 'thead', 'tbody', 'tr', 'th', 'td', 'div']);
    return td;
}

/**
 * Convert an HTML string to Markdown.
 * Angular bindings are stripped first; @@FNREF_N@@ tokens are converted to
 * [^N] references after Turndown runs.
 */
function htmlToMd(html, turndown) {
    if (!html || typeof html !== 'string') return '';
    const cleaned = stripAngularBindings(html);
    const md = turndown.turndown(cleaned).trim();
    // Turndown may escape the underscore to \_ so match both variants.
    let result = md.replace(/@@FNREF\\?_(\d+)@@/g, '[^$1]');
    // Turndown escapes literal [ and ] in body text; restore them.
    result = result.replace(/\\\[/g, '[').replace(/\\\]/g, ']');
    return result;
}

function main() {
    const inputPath = process.argv[2];
    const outputPath = process.argv[3] || (inputPath ? inputPath.replace(/\.json$/i, '.md') : 'intro.md');

    if (!inputPath) {
        console.error('Missing input JSON path.');
        console.error(
            'Example: node scripts/convert-intro-to-md.cjs src/assets/.../intro.json src/assets/.../intro.md'
        );
        process.exit(1);
    }

    const raw = fs.readFileSync(inputPath, 'utf8');
    const json = JSON.parse(raw);

    const introItems = Array.isArray(json?.intro) ? json.intro : [];
    if (introItems.length === 0) {
        console.error('No intro array found in input JSON.');
        process.exit(1);
    }

    const turndown = createTurndown();
    const out = [];
    const allFootnotes = new Map(); // noteNum (string) -> inner HTML

    for (const introEntry of introItems) {
        const entryId = introEntry?.id || '';
        const blocks = Array.isArray(introEntry?.content) ? introEntry.content : [];

        if (entryId) {
            out.push(`# Intro ${entryId}`);
            out.push('');
        }

        for (const block of blocks) {
            const header = (block?.blockHeader || '').trim();
            const fragments = Array.isArray(block?.blockContent) ? block.blockContent : [];
            const notes = Array.isArray(block?.blockNotes) ? block.blockNotes : [];

            if (header) {
                out.push(`## ${header}`);
                out.push('');
            }

            for (const fragment of fragments) {
                // Replace footnote-ref anchors with tokens BEFORE Turndown so
                // that Turndown does not escape the [^N] square brackets.
                const withTokens = replaceFootnoteRefs(fragment);
                const md = htmlToMd(withTokens, turndown);
                if (md) {
                    out.push(md);
                    out.push('');
                }
            }

            // Collect footnotes from blockNotes; first occurrence wins.
            for (const [num, html] of parseBlockNotes(notes)) {
                if (!allFootnotes.has(num)) {
                    allFootnotes.set(num, html);
                }
            }
        }
    }

    if (allFootnotes.size > 0) {
        out.push('---');
        out.push('');

        // Output footnotes in numeric order.
        const sorted = [...allFootnotes.entries()].sort((a, b) => Number(a[0]) - Number(b[0]));
        for (const [num, html] of sorted) {
            const noteText = htmlToMd(html, turndown);
            out.push(`[^${num}]: ${noteText}`);
            out.push('');
        }
    }

    const finalMd = normalizeWhitespace(out.join('\n')) + '\n';

    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, finalMd, 'utf8');

    console.log(`Converted: ${inputPath}`);
    console.log(`Written:   ${outputPath}`);
}

main();
