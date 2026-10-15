#!/usr/bin/env python3
"""Generate portable editions and an allowlisted, reproducible skill archive.

Python standard library only. Does not install skills, use the network or delete files.
"""
import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://github.com/yanlin-zhou/beer-buddy'
SOURCE_FILES = [
    'SKILL.md', 'references/stories.json', 'references/stories.md',
    'references/phrases.md', 'references/principles.md', 'references/styles.md',
    'references/service.md', 'references/tasting.md', 'references/menu.md', 'templates/outputs.md', 'agents/openai.yaml',
]
PACKAGE_FILES = SOURCE_FILES + [
    'VERSION', 'LICENSE', 'README.md', 'START.md', 'PROMPT.md',
    'docs/INSTALL.md', 'docs/VALIDATION.md', 'docs/RELEASE_REVIEW.md', 'docs/V1.1_RESEARCH.md', 'docs/MENU_MODE.md',
    'CONTRIBUTING.md', 'CHANGELOG.md', 'scripts/release.py',
    'tests/test_release.py', 'evals/evals.json', 'evals/smoke-cases.json',
    'evals/results/text-smoke.json', 'evals/results/portable.json', 'evals/results/retests.json',
    'evals/v1.1-tasting.json', 'evals/results/v1.1-tasting.json', 'evals/results/v1.1-entries.json',
    'evals/v1.2-menu.json', 'evals/results/v1.2-menu.json',
    'evals/v1.2.1-single-beer.json', 'evals/results/v1.2.1-single-beer.json',
]


def read(name):
    return (ROOT / name).read_text(encoding='utf-8')


def validate():
    version = read('VERSION').strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('VERSION must be a semantic version')
    skill = read('SKILL.md')
    if not skill.startswith('---\nname: beer-buddy\ndescription: '):
        raise ValueError('SKILL.md frontmatter is missing name or description')
    for target in re.findall(r'\]\(([^)]+)\)', skill):
        if not target.startswith(('https://', '#')) and not (ROOT / target).is_file():
            raise ValueError('SKILL.md missing reference: ' + target)
    data = json.loads(read('references/stories.json'))
    if data.get('skill_version') != version:
        raise ValueError('stories.json skill_version does not match VERSION')
    ids = set()
    fields = ['id', 'title', 'kind', 'triggers', 'hook', 'spoken', 'memory_beats',
              'optional_bridge', 'stop_rule', 'fact_core', 'source_url',
              'source_kind', 'verified_at', 'caveats']
    for story in data['stories']:
        for field in fields:
            if not story.get(field):
                raise ValueError(story.get('id', '?') + ': missing ' + field)
        if story['id'] in ids:
            raise ValueError('Duplicate story id: ' + story['id'])
        ids.add(story['id'])
        if story['kind'] not in ['story', 'observation', 'legend']:
            raise ValueError(story['id'] + ': invalid kind')
        if len(story['memory_beats']) != 3:
            raise ValueError(story['id'] + ': expected three memory_beats')
        if not story['source_url'].startswith('https://'):
            raise ValueError(story['id'] + ': invalid source_url')
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', story['verified_at']):
            raise ValueError(story['id'] + ': invalid verified_at')
        if story['kind'] == 'legend' and not all('传说' in story[k] for k in ['hook', 'spoken']):
            raise ValueError(story['id'] + ': legend must be labelled in spoken text')
        for field in ['spoken', 'source_url']:
            if story[field] not in read('references/stories.md'):
                raise ValueError('stories.md differs from stories.json: ' + story['id'] + '/' + field)
    return version, skill, data


def portable(text):
    # References are embedded below; no filesystem access is required by the reader.
    return re.sub(r'\[([^\]]+)\]\((?!https?://|#)[^)]+\)', r'\1（见本文件相应部分）', text)


def full_prompt(version, skill, data):
    body = skill.split('---', 2)[2].strip()
    parts = [
        '# 啤酒搭子 · 完整单文件版\n',
        f'版本 {version} · 从仓库源文件自动生成，请勿单独修改。\n',
        '把此文件上传到支持读取文本附件的 AI 对话，再说：请按文件中的啤酒搭子帮我。'
        '也可复制全文到容量足够的新对话；无需把它塞进长度受限的自定义指令。'
        '模型和图片能力取决于你使用的平台；本文件没有外部工具依赖。\n',
        '以下是完整指令与使用所需的参考资料，直接查阅相应部分，不要求用户另找文件。\n',
        portable(body),
    ]
    for name in ['references/stories.md', 'references/phrases.md', 'references/principles.md',
                 'references/styles.md', 'references/service.md', 'references/tasting.md', 'references/menu.md', 'templates/outputs.md']:
        material = read(name)
        if name == 'references/stories.md':
            material = re.sub(r'机器可读版本：\[stories.json\]\(stories.json\)。', '', material)
            material = material.split('\n## 给维护者\n', 1)[0].rstrip()
        parts.extend(['\n---\n', '资料部分：' + name + '\n', portable(material)])
    return '\n\n'.join(parts).rstrip() + '\n'


def starter_section(name):
    material = read(name)
    begin, end = '<!-- STARTER:BEGIN -->', '<!-- STARTER:END -->'
    if material.count(begin) != 1 or material.count(end) != 1 or material.index(begin) >= material.index(end):
        raise ValueError(name + ' must contain one ordered STARTER:BEGIN/END pair')
    content = material.split(begin, 1)[1].split(end, 1)[0].strip()
    if not content:
        raise ValueError(name + ' starter content is empty')
    return content


def starter(version, data):
    chosen = ['guinness-records-origin', 'qingdao-beer-in-a-bag', 'happy-hops-returning-character', 'alvarado-unexpected-reader-award']
    stories = {s['id']: s for s in data['stories']}
    lines = [
        '# 先试这一杯\n',
        f'啤酒搭子 {version} 的轻量体验版。复制下面代码框的全部文字，发给你正在用的 AI，再补一句你的场景。'
        '不用安装，也不用先懂精酿。\n',
        '> 例如：我手里是 Happy Hops IPA，介绍一下，让我喝起来有点意思，别像背课本。\n',
        '```text',
        '请做我的“啤酒搭子”：我拍单款酒或泛问介绍时，讲一个这款酒或酒厂的小故事，顺手告诉我一个喝起来值得留意的地方。'
        '目标是让我放下手机，用自己的话讲；对方也能轻松接话或不接。',
        '先完成我这次的明确要求。要一句就一句，要故事就一个故事，别先让我填问卷。'
        '单杯泛介绍通常三四句，故事与一个观察都保留；只问品饮或只听故事时通常两三句。整张酒单给少量不同理由的候选。来源短放在后面，不给同一回复的多个改写版本。需要练习时才给三个记忆词。',
        '保留我的真实感受，可以说“我觉得苦”。不要编我的味觉、经历、酒保引语、酒厂历史或参数。'
        '看不清图片就说看不清；没有图片能力请让我打出酒名。',
        '有人聊音乐就接音乐，不必拉回酒；没接话时允许停下，不猜对方心理。确实错了就简短承认，双方说法未核实就先确认。'
        '不排口味高低，不强制每句提问，不让不饮酒的人必须尝一口。记录和结束时不追加下一杯。',
        '知识范围是啤酒；其他酒局可以帮我自然接话，不冒充其他酒类专家。'
        '我表示不喝、已喝够或要开车时不推荐含酒精饮品，仍可聊故事。',
        '优先用下面有来源的材料。没确认品牌就明确当作别的品牌例子。品牌自述说“酒厂讲过”，'
        '传说必须说是传说；查不到的别编。没有合适材料可聊已知生活话题。',
        starter_section('references/tasting.md'),
        starter_section('references/menu.md'),
    ]
    for sid in chosen:
        s = stories[sid]
        lines.extend(['', s['title'], s['spoken'], '依据：' + s['source_url'],
                      '记忆词（仅需要时给）：' + ' → '.join(s['memory_beats']),
                      '边界：' + ' '.join(s['caveats']).replace('hook 和 spoken 的传说标签', '讲述中的“传说”限定')])
        if s.get('followup'):
            lines.append('可选后续：' + s['followup'])
    lines.extend(['```', '',
                  f'这版带 {len(chosen)} 条故事、单杯故事加品饮与多角度酒单入口，适合先体验。完整版本带 {len(data["stories"])} 条素材和品饮、选酒、采购等参考资料：'
                  '[完整单文件版](PROMPT.md) · [安装 Skill](docs/INSTALL.md)。', '',
                  '可以接着说：“菜单从几个角度挑”“只选一款”“我没闻到，只觉得苦”“只讲一个故事”。', '',
                  f'[回到项目]({URL}) · 由 scripts/release.py 生成。'])
    return re.sub(r'\n{3,}', '\n\n', '\n\n'.join(lines)) + '\n'


def write_archive(version):
    missing = [name for name in PACKAGE_FILES if not (ROOT / name).is_file()]
    if missing:
        raise ValueError('Missing release files: ' + ', '.join(missing))
    dest = ROOT / 'dist'
    dest.mkdir(exist_ok=True)
    archive = dest / ('beer-buddy-' + version + '.zip')
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name in sorted(PACKAGE_FILES):
            info = zipfile.ZipInfo('beer-buddy/' + name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, (ROOT / name).read_bytes())
    # Release assets are copied, never linked to private workspace files.
    for name in ['START.md', 'PROMPT.md']:
        (dest / name).write_bytes((ROOT / name).read_bytes())
    names = [archive.name, 'START.md', 'PROMPT.md']
    sums = ''.join(hashlib.sha256((dest / n).read_bytes()).hexdigest() + '  ' + n + '\n' for n in names)
    (dest / 'SHA256SUMS').write_text(sums, encoding='utf-8')
    return archive


def check_local_links():
    """Check paths, not remote availability or heading anchors."""
    for name in PACKAGE_FILES:
        path = ROOT / name
        if not path.is_file():
            raise ValueError('Missing release file: ' + name)
        if path.suffix != '.md':
            continue
        for target in re.findall(r'\]\(([^)]+)\)', read(name)):
            if target.startswith(('https://', 'http://', '#', 'mailto:')):
                continue
            target = target.split('#', 1)[0]
            if target and not (path.parent / target).is_file():
                raise ValueError(name + ': broken local link ' + target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check sources and generated editions without writing')
    parser.add_argument('--generate-only', action='store_true', help='Generate editions without packaging')
    args = parser.parse_args()
    try:
        version, skill, data = validate()
        outputs = {'PROMPT.md': full_prompt(version, skill, data), 'START.md': starter(version, data)}
        for name, content in outputs.items():
            if args.check:
                if not (ROOT / name).is_file() or read(name) != content:
                    raise ValueError(name + ' is stale; run python3 scripts/release.py')
            else:
                (ROOT / name).write_text(content, encoding='utf-8')
        if args.check:
            check_local_links()
            print('Source schema, references, versions and generated editions: OK')
        elif args.generate_only:
            print('Generated START.md and PROMPT.md')
        else:
            check_local_links()
            print('Built ' + str(write_archive(version).relative_to(ROOT)))
        return 0
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as error:
        print('Release validation failed: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
