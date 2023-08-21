---
title: Dextensify: Disabling Admin-Installed Chrome Extensions From Any Webpage
date: 8/20/23
description: When Chrome OS v115 released, Google formally patched LTMEAT by disabling chrome://kill and chrome://hang. But what if you could find a way to avoid those pesky Chrome URLs?
url: https://ading.dev/blog/posts/ltmeat_generic.html
---

## Introduction:
Back in May 2023, [LTMEAT](https://ltmeat.bypassi.com) was all the rage, letting you disable admin extensions extremely easily. All it required was the use of `chrome://kill` and `chrome://hang`. Unfortunately, when Chrome v115 rolled around, Google [disabled these debug URLs](https://chromium-review.googlesource.com/c/chromium/src/+/4558108), putting an end to the exploit's usability. But what if you could find a way to avoid those pesky Chrome URLs?

## A Refresher on LTMEAT:
All resources that belong to a Chrome extension share the same process. Thus, if any of the extension's pages were to freeze, then the entire extension would also be frozen. The easiest way to achieve this would be to navigate to `chrome://hang` in the address bar, which hangs the current page. However, simply hanging a Chrome extension has the side effect of also freezing any event listeners, blocking any other webpages from loading. 

To get around this, you can kill the extension's process right after you hang it (using `chrome://kill`), then hang it again to prevent the listeners from being registered. By preventing the extension from reloading, then you've functionally disabled it.

## Getting Around the Patch:
The patch that Chrome v115 included simply disabled the use of `chrome://kill` and `chrome://hang` (as well as a few related URLs), and the underlying issues were not fixed. So how do we accomplish the same things without using any Chrome URLs?

Killing an extension is fairly straightforward. On the details page of an extension in `chrome://extensions`, there's a switch which toggles an extension's access to `file://` URLs. Simply flipping that switch will kill the extension's process and force it to restart.

![The file URL access switch](/blog/assets/dextensify/file_url_switch.png)

Hanging an extension is slightly trickier, although just like with the original LTMEAT, a convenient Chrome feature makes this possible.

## Web Accessible Resources:
If you've ever viewed an extension's `manifest.json`, you may have seen a field called [`web_accessible_resources`](https://developer.chrome.com/docs/extensions/mv3/manifest/web_accessible_resources/) somewhere towards the bottom of the file. The purpose of this is to allow other pages to view some of the extension's resources. For instance, if an extension contained the following in its manifest, then  any path under `chrome-extension://extensionidhere/public/` would be accessible to any regular webpage.

```
"web_accessible_resources": [
  "public/*"
]
```

Any web accessible resources can also be put inside an iframe. However, since all extension resources share a single process, any iframe of an extension resource will be part of the main extension process. Thus, by constantly creating new iframes to a web accessible resource, you can effectively freeze the entire extension. Since you are able to do this from any webpage, this allows us to bypass the `chrome://hang` block.

## Implementing the Exploit:
Obviously, you can't endlessly create iframes without the browser running out of memory and freezing. Previously created iframes have to be removed, although it's not as simple as just calling `.remove()` on them. Chrome also doesn't seem to be able to properly garbage collect removed iframes (and when it does, it happens after a delay), which leads to a memory leak.

My workaround for this was to gradually decrease the rate that the iframes were created at so that Chrome's garbage collection has a chance to catch up, and this seems to work most of the time. I then wrote some HTML and CSS to wrap it all up, as well as a small Python script to generate the data URL.

## The Final Result:
Here's what the finished exploit page looks like:

![A screenshot of the finished exploit](/blog/assets/dextensify/dextensify_screenshot.png)

It's currently being hosted at [dextensify.ading.dev](https://dextensify.ading.dev/), and the source code is also available on my [Github](https://github.com/ading2210/dextensify). 

I'm honestly sort of impressed that the workaround to Google's patch is as simple as spamming iframes, but that's just Chrome for you. It happened last time with LTMEAT, and I'm sure more of these simple bugs will be found in the future.