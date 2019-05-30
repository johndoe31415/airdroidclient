# airdroidclient
I needed a way to download pictures off my smart phone using a script.
Unfortunately, there's nothing in stock Android that allows you to do that and
MTP is excruciatingly slow. There's the Airdroid smart phone app that starts a
web server on the phone and opens a UI that you can surf to, but I didn't want
to use the UI. Therefore I reverse engineered the underlying API and used it
directly

## Airdroid security
The security implementation is pretty horrific and I do not condone the
"security" features in any way. They use single DES with an ECB operating mode
and have numerous padding oracles that the API exposes. Do not rely on that
security for anything at all, it's entirely broken.

# License
GNU GPL-3.
