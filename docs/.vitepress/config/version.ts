import fs from "fs";
import { execSync } from "child_process";

import {
    githubReleasesApi,
    githubReleasesPage,
    interfaceJsonPath,
    changelogPath,
    releaseMetaPath,
} from "./constants";

type InterfaceConfig = {
    version?: string;
};

type GitHubRelease = {
    draft?: boolean;
    tag_name?: string;
    html_url?: string;
    published_at?: string;
};

type StoredReleaseMeta = {
    tag_name?: string;
    html_url?: string;
    published_at?: string;
};

export type ReleaseMeta = {
    version: string;
    link: string;
    body?: string;
    bodyFingerprint?: string;
    published_at?: string;
};

const interfaceConfig = JSON.parse(
    fs.readFileSync(interfaceJsonPath, "utf-8"),
) as InterfaceConfig;

function computeFingerprint(s: string): string {
    let hash = 0
    for (let i = 0; i < s.length; i++) {
        const ch = s.charCodeAt(i)
        hash = ((hash << 5) - hash) + ch
        hash |= 0
    }
    return Math.abs(hash).toString(16)
}

function readChangelog(): string {
    try {
        return fs.readFileSync(changelogPath, "utf-8")
    } catch {
        return ""
    }
}

function getChangelogDate(): string {
    try {
        return execSync(
            `git log -1 --format=%aI -- "${changelogPath}"`,
            { encoding: "utf-8" },
        ).trim()
    } catch {
        return ""
    }
}

function readStoredReleaseMeta(): StoredReleaseMeta | null {
    try {
        return JSON.parse(
            fs.readFileSync(releaseMetaPath, "utf-8"),
        ) as StoredReleaseMeta
    } catch {
        return null
    }
}

async function getLatestReleaseMeta(): Promise<ReleaseMeta> {
    const body = readChangelog()
    const published_at = getChangelogDate() || undefined

    // 优先使用 release 事件写入的版本信息，保证文档站只在发布后更新。
    const stored = readStoredReleaseMeta()
    if (stored?.tag_name) {
        console.log(`[docs] release version: ${stored.tag_name} (from release.json)`)
        return {
            version: stored.tag_name,
            link: stored.html_url ?? githubReleasesPage,
            body: body || undefined,
            bodyFingerprint: body ? computeFingerprint(body) : undefined,
            published_at: stored.published_at ?? published_at,
        }
    }

    try {
        const response = await fetch(githubReleasesApi, {
            headers: {
                Accept: "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            signal: AbortSignal.timeout(3000),
        });

        if (!response.ok) {
            throw new Error(`GitHub API responded with ${response.status}`);
        }

        const releases = (await response.json()) as GitHubRelease[];
        const latestRelease = releases.find(
            (release) => !release.draft && typeof release.tag_name === "string",
        );

        if (latestRelease?.tag_name) {
            console.log(`[docs] release version: ${latestRelease.tag_name} (from GitHub API)`)
            return {
                version: latestRelease.tag_name,
                link: latestRelease.html_url ?? githubReleasesPage,
                body: body || undefined,
                bodyFingerprint: body ? computeFingerprint(body) : undefined,
                published_at: latestRelease.published_at ?? published_at,
            };
        }
    } catch {
        // Keep local docs builds working when GitHub is unreachable.
    }

    console.log(`[docs] release version: ${interfaceConfig.version ?? "unknown"} (from interface.json)`)
    return {
        version: interfaceConfig.version ?? "unknown",
        link: githubReleasesPage,
        body: body || undefined,
        bodyFingerprint: body ? computeFingerprint(body) : undefined,
        published_at,
    };
}

export const latestReleaseMeta = await getLatestReleaseMeta();
