# GitHub Mirror

HACS custom repositories must be public GitHub repositories. The canonical project can stay on GitLab, but GitLab CI can publish the default branch and tags to a GitHub mirror.

## GitHub Setup

1. Create an empty public GitHub repository, for example:

   ```text
   https://github.com/<owner>/ha-weather-provider
   ```

   If you initialize the repository with a README, keep track of its default branch name and set `GITHUB_SYNC_BRANCH` below.

2. Create a fine-grained GitHub token for that repository.
3. Grant the token **Contents: Read and write** access.

## GitLab CI Variables

Add these variables in GitLab under **Settings** > **CI/CD** > **Variables**:

| Variable | Value | Notes |
| --- | --- | --- |
| `GITHUB_SYNC_REPOSITORY` | `<owner>/ha-weather-provider` | Do not include `https://github.com/`. |
| `GITHUB_SYNC_TOKEN` | GitHub token value | Mark as masked and protected if the default branch is protected. |
| `GITHUB_SYNC_BRANCH` | `main` or `master` | Optional. Defaults to the GitLab default branch. |

## Sync Behavior

The `sync-github` job runs only on the GitLab default branch and only when both required GitHub variables are present. It pushes:

- The current default branch commit to `GITHUB_SYNC_BRANCH`, or to the same branch name on GitHub when `GITHUB_SYNC_BRANCH` is unset.
- All repository tags.

The job does not push merge request branches. GitLab remains the canonical development remote.

## HACS URL

After the first successful sync, use the GitHub mirror URL as the HACS custom repository URL:

```text
https://github.com/<owner>/ha-weather-provider
```
