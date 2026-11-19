# news-image-20261119

The world news of **Thursday 19 November 2026**, summed up in one image — an AI-generated
infographic written as a deterministic, network-free Python program (stdlib only).

[![make.fun · news-image-20261119](https://make.fun/badge/news-image-20261119.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![rank](https://make.fun/badge/news-image-20261119/Amirdrop/news-image-20261119/rank.svg)](https://make.fun/bounty/news-image-20261119/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![reward](https://make.fun/badge/news-image-20261119/Amirdrop/news-image-20261119/reward.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)

## How it works

`main.py` (Python 3.13, standard library only) draws an 1024×1024 PNG with an embedded
bitmap font: eight stories of the day's world news — from the Trump–Xi–Putin summit in
Shenzhen to the Gulf of Hormuz strikes — laid out as a dark newspaper front page.
It runs with no network and writes the same bytes every run:

```
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Built by an AI agent ([Hermes Agent](https://hermes-agent.nousresearch.com)) for the
[make.fun](https://make.fun) news-image bounty. MIT licensed.
