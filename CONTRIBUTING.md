# How to contribute
## Read the documentation
Ensure you have read any appropriate documentation for using or developing SMIB and SMIBHID in the [SMIB readme](https://github.com/somakeit/smib/blob/master/README.md) and [SMIBHID readme](https://github.com/somakeit/smibhid/blob/master/README.md)

## Bugs
Open our [issue tracker](https://github.com/somakeit/smibhid/issues) and create a new issue giving us much detail about the bug as possible, how to recreate it, what outcome you expected vs what outcome you got. You can label this issue with the "bug" label.

## Enhancement ideas
If you have a new idea, create an [issue](https://github.com/somakeit/smibhid/issues) with details of what you would like to see and why it would be helpful and tag the issue with the "enhancement" label.

## Writing patches
If you would like to contribute some code back to the project you are welcome to make a pull request. Ensure an issue exists for your proposed patch and drop a comment in there to let us know you are working on it. Create a fork of the repository, create a new branch for your patch and use that branch to raise a pull request. See the [github documentation](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request) for more information.

### Code conventions
In general we follow [pep8 guidelines](https://peps.python.org/pep-0008/).

Code should be clear in its intent with minimal comments, ensure you use helpful variable and function names and keep functions and methods simple in their scope. More well named simple functions are better than monolithic complex functions with short and cryptic names.

A code update should almost always trigger an update or creation of new documentation; Ensure associated documentation is updated whenver possible with new code patches.

### Tests
We haven't got tests yet, but if we do it will be pytest, feel free to provide pytests for your patch.

### Pull request approval
Pull requests will be reviewed by repo admins (code club) at SoMakeIt and providing at least one repo admin approves a review, the code will be merged into the master branch for use on bleeding edge devices. Periodically a release will be created of recent master branch PRs that have been running in production OK.