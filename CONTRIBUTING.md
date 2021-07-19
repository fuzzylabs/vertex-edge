# Contributing to vertex:edge

First off, thanks for taking the time to contribute!

This article will help you get started, from learning [how you can contribute](#how) all the way to raising your first [pull request](#firstcontrib).

## Contents

* [How can I contribute?](#how)
* [Your first code contribution](#firstcontrib)
* [Style guides](#styleguides)

<a name="how"></a>
## How can I contribute?

### Testing

This is a new project that is moving fast, and so one of the most useful ways you can help out is simply testing the tools and the documentation in order to tease out bugs, edge-cases and opportunities to improve things.

If you are testing this out, whether in production or not, we're really keen to hear from you and to receive your feedback.

### Reporting bugs

Sadly, bugs happen; we're sorry! Before reporting a bug, please check the [open issues](https://github.com/fuzzylabs/vertex-edge/issues) to see if somebody has submitted the same bug before. If so, feel free to add further detail to the existing issue.

If your bug hasn't been raised before then [go ahead and raise it](https://github.com/fuzzylabs/vertex-edge/issues/new?assignees=&labels=bug&template=bug_report.md&title=) using our bug report template. Please provide as much information as possible to help us to reproduce the bug.

### Suggesting enhancements

Enhancements and feature requests are very much welcome. We hope to learn from real-world useage which features are missing so that we can improve the tool to meet the expectations of real machine learning projects. Please use our [feature request template](https://github.com/fuzzylabs/vertex-edge/issues/new?assignees=&labels=enhancement&template=feature_request.md&title=) to do this.

### Taking on an existing issue

You'll find plenty of opportunities to contribute amount our [open issues](https://github.com/fuzzylabs/vertex-edge/issues). If you'd like to pick up an issue, please add a comment saying so, as this avoids duplicate work. Then read on to make your [first code contribution](#firstcontrib).

<a name="firstcontrib"></a>
## Your first code contribution

### Fork the repository

We prefer that you fork the repository to your own Github account first before raising a pull request.

### Pull requests

Once you've got a code change that's ready to be reviewed, please raise a pull request. If you've got some ongoing work that's not quite ready for review, feel free to raise the pull request, but please place `[WIP]` (work-in-progress) in front of the PR title so we know it's still being worked on.

Please include a description in the pull request explaining what has been changed and/or added, how, and why. Please also link to relevant issues and discussions where appropriate.

<a name="styleguides"></a>
## Style guides

### Git commit messages

* Make sure it's descriptive, so not `fix bug` but `fix issue #1234 where servers spontaeously combusted on random Tuesdays`.
* Keep the first line brief; use multiple lines if you want to add more details.
* Reference relevant issues, discussions and pull requests where appropriate.

### Python code

* Above all, write clean, understandable code.
* Use [black](https://github.com/psf/black) and [PyLint](https://pypi.org/project/pylint) to help ensure code is consistent.

### Documentation

* Use [Markdown](https://guides.github.com/features/mastering-markdown)
* Place a table of contents at the top of each Markdown file.
* Write concise, clear explanations.
