# github-authn-checker

Companion app for GitHub Enterprise SAML + OAuth AuthN issue.

Will request `read:org` scope from GitHub and then check if every known organizations membership status is readable.

A non-readable membership status indicates the organization is SAML protected and the user does not have a SAML session.

[Read the original article here](https://notes.acuteaura.net/posts/github-enterprise-security/)

[Try the app here](https://github-authn-checker.fly.dev/)

This is my first Flask _and_ my first Python app. Critiques welcome in the issues :)