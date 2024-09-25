# Status changes to "QA Testing" if a pull request is merged

GitHub doesn't provide a built-in way to update the status if a pull request is merged. This
GitHub Action aims to address this by allowing you to update the project status within a central GitHub project.

## Introduction

This GitHub Action allows you to manage status changes for issues in a central GitHub project. It integrates with a custom
text field (status) that you can add to your GitHub project board. 

### Prerequisites

Before you can start using this GitHub Action, you'll need to ensure you have the following:

1. A GitHub repository where you want to enable this action.
2. A GitHub project board (name: Requests Product Backlog) with a custom status field added.
3. A "QA Testing" status option added in the Status field.
4. A Token (Classic) with permissions to repo:*, write: org, read: org, read:user, user:email, project. 

### Inputs

| Input                                | Description                                                                                      |
|--------------------------------------|--------------------------------------------------------------------------------------------------|
| `gh_token`                           | The GitHub Token                                                                                 |
| `project_number`                     | The project number                                                                               |                                                          
| `status_field_name` _(optional)_     | The status field name. The default is `Status`                                                   |
| `notification_type` _(optional)_     | The notification type. Default is `comment`          |
| `enterprise_github` _(optional)_     | `True` if you are using enterprise github and false if not. Default is `False`                   |
| `repository_owner_type` _(optional)_ | The type of the repository owner (oragnization or user). Default is `user`                       |
| `dry_run` _(optional)_               | `True` if you want to enable dry-run mode. Default is `False`                                    |


### Examples

