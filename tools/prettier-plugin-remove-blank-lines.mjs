/**
 * Prettier plugin: removes blank lines from JSON.
 * preprocess hook only - does NOT change any formatting rules.
 */
import { parsers as babelParsers } from "prettier/plugins/babel";

function removeBlanks(text) {
    return text.replace(/\n\s*\n/g, "\n");
}

export const languages = [
    { name: "json", parsers: ["json"] },
    { name: "jsonc", parsers: ["jsonc"] },
];

export const parsers = {
    json: {
        ...babelParsers.json,
        preprocess: removeBlanks,
    },
    jsonc: {
        ...babelParsers.jsonc,
        preprocess: removeBlanks,
    },
};
