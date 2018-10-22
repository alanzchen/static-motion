# 🚀 Static Motion [DISCONTINUED]

Make your static site from [Notion.so](https://notion.so) with the help of Netlify and Travis CI.

[![Build Status](https://travis-ci.org/alanzchen/static-motion.svg?branch=master)](https://travis-ci.org/alanzchen/static-motion)

**Demo:**

- [Project Homepage](https://staticmotion.zenan.ch)
- [Disqus Integration](https://staticmotion.zenan.ch/disqus-integration-demo)

## Installation

How do I install this… **No! You do not need to install it on your machine.**

All you need is a Github account.

## Get Started

1. Fork this project.
2. Turn on Travis CI for your forked repository.
3. Get your access token at Netlify and set the following environment variables on Travis CI's setting page:
   See `conf.py` for example.
   - `ACCESS_TOKEN`: fill your Netlify access token.
      (Remember to secure it!)
   - `SITE_ID`: The "API ID" of your Netlify site.
   - `index`: The URL of your index page on [Notion.so](https://notion.so).
   - `title_sep`: Your title separator. No space around!
   - `description`: Your site description. "Remember to quote your string!"
   - `base_url`: Your site URL.
   - `twitter`: Your twitter ID.
      Declare an empty string if you do not want it.
   - `build_mobile`: Will build a mobile version of your entire site at /m/ if this option presents.
   - `apple_touch_icon`: the URL of your `apple-touch-icon.png` hosted externally.
   - `favicon`: the URL of your `favicon.ico` hosted externally.
   - `anchor`: Enable anchor detection if this option presents. All urls starting with `https://www.notion.so` with `#` somewhere in the url will be rewritten to your relative path.
4. Bang! Wait a few minutes and your site will be up!
5. Want to have Google Analytics and Disqus? See [customization](https://staticmotion.zenan.ch/customization).

## Updating Your Site

You can set up [cron jobs](https://docs.travis-ci.com/user/cron-jobs/) in your Travis CI project. However, if you wish to update your site immediately, please manually rebuild your project in Travis CI.

Committing directly to your Github repository to trigger Travis CI rebuild **is highly discouraged**.

## Upgrading Your Static Motion

Simply merge this repository with your repository.

## Debugging

As [notion.so](https://notion.so) make changes to their template, this utility may break at any time.

Before you go, make sure you have:

- Python 3.6,
- the latest Google Chrome,
- a working `chromedriver` .

Once you are ready, clone this repo and cd into it. Install the dependency:

```
pip install -r requirements.txt
```

Then run the static site generator.

```
python motion.py
```

## Known Issue

- Embedded elements might not work.
  - Embedded tweets are not working.
- Fonts in code blocks may flicker slightly.
- Pages with the same base url but with different hash cannot coexist in the same site.
