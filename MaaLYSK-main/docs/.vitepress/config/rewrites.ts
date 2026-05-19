export function rewriteDocPath(srcPath: string) {
    const match = srcPath.match(/^(zh_cn|en_us)\/(.+?)\/(\d+\.\d+)-.*\.md$/);

    if (match) {
        const [, lang, dir, id] = match;
        return `${lang}/${dir}/${id}.md`;
    }

    return srcPath;
}
