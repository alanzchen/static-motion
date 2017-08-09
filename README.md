# 🚀 Static Motion

Make your static site from [Notion.so](notion.so) with the help of Netlify and Travis CI.

[![Build Status](https://travis-ci.org/alanzchen/static-motion.svg?branch=master)](https://travis-ci.org/alanzchen/static-motion)

**Demo:**

- [Project Homepage](staticmotion.zenan.ch)
- [Disqus Integration](https://static-motion.zenan.ch/disqus-integration-demo)

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
   - `index`: The URL of your index page on [Notion.so](notion.so).
   - `title_sep`: Your title separator. No space around!
   - `description`: Your site description. "Remember to quote your string!"
   - `base_url`: Your site URL.
   - `twitter`: Your twitter ID.
      Declare an empty string if you do not want it.
   -  `apple_touch_icon`: the URL of your `apple-touch-icon.png` hosted externally.
   -  `favicon`: the URL of your `favicon.ico` hosted externally.
4. Bang! Wait a few minutes and your site will be up!
5. Want to have Google Analytics and Disqus? See [customization](https://static-motion.zenan.ch/customization).

## Debugging

As [notion.so](notion.so) make changes to their template, this utility may break at any time.

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