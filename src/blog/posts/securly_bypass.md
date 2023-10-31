---
title: Bypassing Securly by Manipulating the URL
date: 10/26/23
description: Inside the source code of the Securly chrome extension, there's a few oversights which could be abused. This blog post will mainly focus on the ones that involve modifying the URL of the blocked page. 
url: https://ading.dev/blog/posts/securly_bypass.html
--- 

## Introduction:
Securly is a web filtering company primarily targeting K-12 schools. Their main product is a Chrome extension for blocking pages on school-owned Chromebooks. If you look into the extension's source code, however, you'll find a few oversights which could be abused. This blog post will mainly focus on the ones that involve modifying the URL of the blocked page.

## Making a Website Unblockable:
Inside Securly's background JS file, there's a function called `isBlockingInProgress`. This is responsible for checking to see if a page is in the process of being blocked. If this returns `true` on a particular URL, then Securly won't bother filtering the page, as it'll assume that it's already doing so.

Here's what the function looks like, with the variable names altered for readability:
```js
function isBlockingInProgress(tabId, url) {
  return new Promise(function (resolve, reject) {
    chrome.tabs.get(tabId, function (tab) {
      if (tab && tab.status == "loading") {
        var host = new URL(url).hostname;
        if (host.indexOf("securly.com") != -1 || host.indexOf("iheobagjkfklnlikgihanlhcddjoihkg") != -1) {
          return void resolve(true);
        }
        if (tab.pendingUrl !== undefined && ((host = new URL(tab.pendingUrl).hostname).indexOf("securly.com") != -1 || host.indexOf("iheobagjkfklnlikgihanlhcddjoihkg") != -1)) {
          return void resolve(true);
        }
      }
      resolve(false);
    });
  });
}
```

These four lines are the important bit:
```js
var host = new URL(url).hostname;
if (host.indexOf("securly.com") != -1 || host.indexOf("iheobagjkfklnlikgihanlhcddjoihkg") != -1) {
  return void resolve(true);
}
```

The `host` variable is set to the URL's [hostname](https://developer.mozilla.org/en-US/docs/Web/API/URL/hostname), which includes the domain and any subdomains. For example, if the provided URL was `https://a.b.example.com`, then `host` will be set to `a.b.example.com`.

The script then checks to see if `securly.com` or `iheobagjkfklnlikgihanlhcddjoihkg` appears in the hostname, and it'll return `true` of that's the case. Notably, `securly.com` can be *anywhere* in the hostname for this condition to be satisfied, which allows it to be abused.

Due to this oversight, you can just make a subdomain at `securly.com.yourdomain.com`, if you have your own domain. If you don't own a domain, you can register free subdomains at [FreeDNS](http://freedns.afraid.org/). You can also register a domain that ends with `securly.com`, such as, [disablesecurly.com](https://www.disablesecurly.com/). By doing this, when Securly tries to filter your page, the `isBlockingInProgress` function will return `true`, preventing Securly from blocking the page.

## Unblocking a Page by Imitating Google Translate:
There's actually an even easier method to unblock websites, which was found by [`@xcr15_51037`](https://discord.com/users/1148629924899463168). If you simply add `#translate.google.com` to the end of a blocked URL, Securly will ignore its filters and let you visit it. But why does this occur?

Once again, the culprit is in Securly's background JS. In it, there's a function which intercepts every HTTP request that the browser makes, and this is aptly called `onBeforeRequestListener`. Towards the end of the function, right before the extension asks Securly's servers if a site is blocked, there's this snippet of code. As with before, the variable names have been changed for readability.
```js
if (url.indexOf("translate.google.com") != -1) {
  hostname = extractTranslateHostname(url);
} else {
  (element = document.createElement("a")).href = url;
  hostname = element.hostname.toLowerCase();
}
```

If the extension finds the string `translate.google.com` anywhere in the URL, it'll pass that URL into `extractTranslateHostname`, which will just return `translate.google.com`. By doing this, it essentially overrides the detected hostname and sets it to that of Google Translate rather what it actually is. 

This is reflected in the subsequent HTTP request that is sent to Securly to check whether the page is blocked: 
![A screenshot of the Securly background page open in devtools](/blog/assets/securly_bypass/securly_devtools.png)

I've just visited `https://old.reddit.com/#translate.google.com`, but the extension has overridden the hostname to be `translate.google.com`, so it doesn't block the page.

## Bonus: Bypassing Securly's Proxy Detection:
While I was writing this article, Securly pushed out an update (2.98.55) which implemented a new proxy detection feature. This update added a new content script (`content10.min.js`), which is injected into every website you visit. Inside this file, there is a function which runs every two seconds, checking the DOM for any elements that might be part of a proxy site. 

```js
const o = setInterval(() => {
  if (document.location.origin.includes("securly.com")) {
    clearInterval(o);
  } else {
    //check for proxies and report back to the extension
  }
}, 2000);
```

It looks like they've made the same mistake as before with implementing an overly broad whitelist of their `securly.com` domain. In this case, if the website's [origin](https://developer.mozilla.org/en-US/docs/Web/API/Location/origin), contains `securly.com`, then the interval will be cleared, disabling the proxy detection.

## Conclusion:
It's not a surprise that Securly is repeating their [older mistakes](https://sheeptester.github.io/longer-tweets/securly-bypass/), considering their already dodgy code quality and privacy practices. For a company claiming to be all about "student safety," they sure don't seem to care about actually writing secure code. If you're stuck with Securly, you now have a few more ways to get around their filtering thanks to these mistakes.