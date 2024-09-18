from pprint import pprint
import logging
import requests
import config
import utils

logging.basicConfig(level=logging.DEBUG)  # Ensure logging is set up

def get_repo_issues(owner, repository, status_field_name, after=None, issues=None):
    query = """
    query GetRepoIssues($owner: String!, $repo: String!, $status: String!, $after: String) {
          repository(owner: $owner, name: $repo) {
            issues(first: 100, after: $after, states: [OPEN]) {
              nodes {
                id
                title
                number
                url
                assignees(first:100) {
                  nodes {
                    name
                    email
                    login
                  }
                }
                projectItems(first: 10) {
                  nodes {
                    project {
                      number
                      title
                    }
                    fieldValueByName(name: $status) {
                      ... on ProjectV2ItemFieldSingleSelectValue {
                        id
                        name
                      }
                    }
                  }
                }
              }
              pageInfo {
                endCursor
                hasNextPage
                hasPreviousPage
              }
              totalCount
            }
          }
        }
    """

    variables = {
        'owner': owner,
        'repo': repository,
        'status': status_field_name,
        'after': after
    }

    response = requests.post(
        config.api_endpoint,
        json={"query": query, "variables": variables},
        headers={"Authorization": f"Bearer {config.gh_token}"}
    )

    data = response.json()

    if data.get('errors'):
        print(data.get('errors'))
   
    # Add debug print statement
    pprint(data)

    repository_data = data.get('data', {}).get('repository', {})
    issues_data = repository_data.get('issues', {})
    pageinfo = issues_data.get('pageInfo', {})
    nodes = issues_data.get('nodes', [])

    if issues is None:
        issues = []
    issues = issues + nodes
    if pageinfo.get('hasNextPage'):
        return get_repo_issues(
            owner=owner,
            repository=repository,
            after=pageinfo.get('endCursor'),
            issues=issues,
            status_field_name=status_field_name
        )

    return issues

def get_project_issues(owner, owner_type, project_number, status_field_name, filters=None, after=None, issues=None):
    query = f"""
    query GetProjectIssues($owner: String!, $projectNumber: Int!, $status: String!, $after: String) {{
        {owner_type}(login: $owner) {{
            projectV2(number: $projectNumber) {{
                id
                title
                number
                items(first: 100, after: $after) {{
                    nodes {{
                        id
                        fieldValueByName(name: $status) {{
                            ... on ProjectV2ItemFieldSingleSelectValue {{
                                id
                                name
                            }}
                        }}
                        content {{
                            ... on Issue {{
                                id
                                title
                                number
                                state
                                url
                                assignees(first: 20) {{
                                    nodes {{
                                        name
                                        email
                                        login
                                    }}
                                }}
                            }}
                        }}
                    }}
                    pageInfo {{
                        endCursor
                        hasNextPage
                        hasPreviousPage
                    }}
                    totalCount
                }}
            }}
        }}
    }}
    """

    variables = {
        'owner': owner,
        'projectNumber': project_number,
        'status': status_field_name,
        'after': after
    }

    try:
        response = requests.post(
            config.api_endpoint,
            json={"query": query, "variables": variables},
            headers={"Authorization": f"Bearer {config.gh_token}"}
        )
    
        data = response.json()
    
        if 'errors' in data:
            logging.error(f"GraphQL query errors: {data['errors']}")
            return []
          
        owner_data = data.get('data', {}).get(owner_type, {})
        project_data = owner_data.get('projectV2', {})
        items_data = project_data.get('items', {})
        pageinfo = items_data.get('pageInfo', {})
        nodes = items_data.get('nodes', [])
    
        if issues is None:
            issues = []
    
        if filters:
            filtered_issues = []
            for node in nodes:
                issue_content = node.get('content', {})
                if not issue_content:
                    continue
    
                issue_id = issue_content.get('id')
                if not issue_id:
                    continue

                # Safely get the fieldValueByName and current status
                field_value = node.get('fieldValueByName')
                current_status = field_value.get('name') if field_value else None
       
                # Apply the 'open_only' filter if specified
                if filters.get('open_only') and issue_content.get('state') != 'OPEN':
                    logging.debug(f"Filtering out issue ID {issue_id} with state {issue_content.get('state')}")
                    continue
       
            # Update nodes with the filtered list
            nodes = filtered_issues
    
        # Append filtered nodes to issues
        issues = issues + nodes
    
        if pageinfo.get('hasNextPage'):
            return get_project_issues(
                owner=owner,
                owner_type=owner_type,
                project_number=project_number,
                after=pageinfo.get('endCursor'),
                filters=filters,
                issues=issues,
                status_field_name=status_field_name
            )
    
        return issues
    except requests.RequestException as e:
        logging.error(f"Request error: {e}")
        return []

def get_project_id_by_title(org, project_title):
    query = """
    query($org: String!, $projectTitle: String!) {
      organization(login: $org) {
        projectsV2(first: 10, query: $projectTitle) {
          nodes {
            id
            title
          }
        }
      }
    }
    """
    
    variables = {
        'owner': owner, 
        'projectTitle': project_title
    }

    try:
        response = requests.post(
            config.api_endpoint,
            json={"query": query, "variables": variables},
            headers={"Authorization": f"Bearer {config.gh_token}"}
        )
    
        data = response.json()

        if 'errors' in data:
            logging.error(f"GraphQL query errors: {data['errors']}")
            return None

            
        projects = data['data']['organization']['projectsV2']['nodes']
        for project in projects:
            if project['title'] == project_title:
                return project['id']
        return None

        if project_id:
            logging.info(f"Found project ID: {project_id}")
            return project_id
        else:
            logging.error("Project not found or does not have the specified number.")
            return None

    except requests.RequestException as e:
        logging.error(f"Request error: {e}")
        return None
        

def get_issue_comments(issue_id):
    query = """
    query GetIssueComments($issueId: ID!, $afterCursor: String) {
        node(id: $issueId) {
            ... on Issue {
                comments(first: 100, after: $afterCursor) {
                    nodes {
                        body
                        createdAt
                        author {
                            login
                        }
                    }
                    pageInfo {
                        endCursor
                        hasNextPage
                    }
                }
            }
        }
    }
    """

    variables = {
        'issueId': issue_id,
        'afterCursor': None
    }

    all_comments = []

    try:
        while True:
            response = requests.post(
                config.api_endpoint,
                json={"query": query, "variables": variables},
                headers={"Authorization": f"Bearer {config.gh_token}"}
            )

            data = response.json()

            if 'errors' in data:
                logging.error(f"GraphQL query errors: {data['errors']}")
                break

            comments_data = data.get('data', {}).get('node', {}).get('comments', {})
            comments = comments_data.get('nodes', [])
            all_comments.extend(comments)

            pageinfo = comments_data.get('pageInfo', {})
            if not pageinfo.get('hasNextPage'):
                break

            # Set the cursor for the next page
            variables['afterCursor'] = pageinfo.get('endCursor')

        return all_comments

    except requests.RequestException as e:
        logging.error(f"Request error: {e}")
        return []



def get_issue_timeline(issue_id):
    query = """
    query GetIssueTimeline($issueId: ID!, $afterCursor: String) {
        node(id: $issueId) {
            ... on Issue {
                timelineItems(first: 100, after: $afterCursor) {
                    nodes {
                        __typename
                        ... on CrossReferencedEvent {
                            source {
                                ... on PullRequest {
                                    id
                                    number
                                    mergedAt
                                    url
                                }
                            }
                        }
                    }
                    pageInfo {
                        endCursor
                        hasNextPage
                    }
                }
            }
        }
    }
    """
    
    variables = {
        'issueId': issue_id,
        'afterCursor': None
    }

    all_timeline_items = []

    try:
        while True:
            response = requests.post(
                config.api_endpoint,
                json={"query": query, "variables": variables},
                headers={
                    "Authorization": f"Bearer {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github.v4+json"
                }
            )

            data = response.json()

            if 'errors' in data:
                logging.error(f"GraphQL query errors: {data['errors']}")
                break

            timeline_data = data.get('data', {}).get('node', {}).get('timelineItems', {})
            timeline_items = timeline_data.get('nodes', [])
            all_timeline_items.extend(timeline_items)

            pageinfo = timeline_data.get('pageInfo', {})
            if not pageinfo.get('hasNextPage'):
                break

            # Set the cursor for the next page
            variables['afterCursor'] = pageinfo.get('endCursor')

        return all_timeline_items

    except requests.RequestException as e:
        logging.error(f"Request error: {e}")
        return []

def update_issue_status_to_qa_testing(project_id, item_id, status_field_id, status_name):
    mutation = """
    mutation UpdateIssueStatus($projectId: ID!, $itemId: ID!, $statusFieldId: ID!, $statusName: String!) {
        updateProjectV2ItemFieldValue(input: {
            projectId: $projectId,
            itemId: $itemId,
            fieldId: $statusFieldId,
            value: { singleSelectOptionId: $statusName }
        }) {
            projectV2Item {
                id
            }
        }
    }
    """

    variables = {
        'projectId': project_id,
        'itemId': item_id,
        'statusFieldId': status_field_id,
        'statusName': status_name
    }

    try:
        response = requests.post(
            config.api_endpoint,
            json={"query": mutation, "variables": variables},
            headers={"Authorization": f"Bearer {config.gh_token}"}
        )

        data = response.json()

        if 'errors' in data:
            logging.error(f"GraphQL mutation errors: {data['errors']}")
            return None

        logging.info(f"Updated issue status to '{status_name}' for item ID: {item_id}")
        return data.get('data')

    except requests.RequestException as e:
        logging.error(f"Request error: {e}")
        return None



