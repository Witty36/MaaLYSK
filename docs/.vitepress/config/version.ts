import fs from "fs";

import {
    githubReleasesApi,
    githubReleasesPage,
    interfaceJsonPath,
} from "./constants";

type InterfaceConfig = {
    version?: string;
};

type GitHubRelease = {
    draft?: boolean;
    tag_name?: string;
    html_url?: string;
};

export type ReleaseMeta = {
    version: string;
    link: string;
};

const interfaceConfig = JSON.parse(
    fs.readFileSync(interfaceJsonPath, "utf-8"),
) as InterfaceConfig;

async function getLatestReleaseMeta(): Promise<ReleaseMeta> {
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
            return {
                version: latestRelease.tag_name,
                link: latestRelease.html_url ?? githubReleasesPage,
            };
        }
    } catch {
        // Keep local docs builds working when GitHub is unreachable.
    }

    return {
        version: interfaceConfig.version ?? "unknown",
        link: githubReleasesPage,
    };
}

export const latestReleaseMeta = await getLatestReleaseMeta();
