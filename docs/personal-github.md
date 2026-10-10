# Publish through a personal GitHub account

This project has no configured remote or initial commit. Nothing has been pushed.
Keep the laptop's global Git configuration and work SSH keys unchanged.

1. Sign in to your personal GitHub account in a browser. Create an empty repository
   named `shopping-assistant` under your personal account. Do not initialize it
   with a README, license, or .gitignore.
2. In this project directory, set the author for this repository only:

   ```sh
   git config --local user.name "YOUR PERSONAL NAME"
   git config --local user.email "YOUR VERIFIED PERSONAL OR GITHUB NOREPLY EMAIL"
   git config --local commit.gpgsign false
   ```

3. Review and commit:

   ```sh
   git status --short
   git add .
   git diff --cached --stat
   git commit -m "Initial Shopping Assistant release"
   ```

4. Add an HTTPS remote, so work SSH keys are not used:

   ```sh
   git remote add origin https://github.com/YOUR_PERSONAL_USERNAME/shopping-assistant.git
   git remote -v
   git -c credential.helper= -c credential.username=YOUR_PERSONAL_USERNAME push -u origin main
   ```

   At the password prompt, use a personal GitHub fine-grained access token scoped
   to this repository with Contents read/write and Workflows write (this first
   push includes a GitHub Actions workflow). Do not use your account password or
   put the token in a URL or shell command. The empty credential-helper override
   applies only to this command and bypasses stored work credentials. Repeat
   this override on later pushes if you have not set up separate credentials.

Alternatively copy the clean source to your personal computer and publish there.
After pushing, check GitHub Actions. To create a release, use GitHub's Releases
page and tag `v0.1.1` on the tested commit. Plugin ZIPs generated with a temporary
tunnel URL only work while that tunnel and backend remain running.

References:
- https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
- https://docs.github.com/en/get-started/git-basics/setting-your-username-in-git
