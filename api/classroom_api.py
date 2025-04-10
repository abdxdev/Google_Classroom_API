import requests
from datetime import datetime, timezone
from .appSettings import appSettings


def parse_datetime(dt_str):
    try:
        return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def get_new_item(service, course, item_type, last_check):
    if item_type == "announcements":
        items = service.courses().announcements().list(courseId=course["id"], orderBy="updateTime desc").execute()
    elif item_type == "courseWork":
        items = service.courses().courseWork().list(courseId=course["id"], orderBy="updateTime desc").execute()
    elif item_type == "courseWorkMaterial":
        items = service.courses().courseWorkMaterials().list(courseId=course["id"], orderBy="updateTime desc").execute()

    for item in items.get(item_type, []):
        if parse_datetime(item["updateTime"]) > last_check:
            try:
                json_data = {"course": course, "activity": item, "type": item_type, "is_new": (parse_datetime(item["creationTime"]) - parse_datetime(item["updateTime"])).total_seconds() < 300}
                print(f"New item found:")
                print(json_data)
                response = requests.post(
                    appSettings.webhook_url,
                    headers={"Content-Type": "application/json"},
                    json=json_data,
                )
            except:
                response = requests.post(
                    appSettings.webhook_url,
                    headers={"Content-Type": "application/json"},
                    json={"course": course, "activity": item, "type": item_type, "is_new": True},
                )
            print("Response:", response.status_code, response.text)
        else:
            break


def notify_new_activity(service):
    print("Last check:", appSettings.last_check)
    try:
        last_check = datetime.fromisoformat(appSettings.last_check).replace(tzinfo=timezone.utc) if appSettings.last_check is not None else datetime.now(timezone.utc)
    except:
        appSettings.update("last_check", datetime.now(timezone.utc).isoformat())
        last_check = datetime.fromisoformat(appSettings.last_check).replace(tzinfo=timezone.utc)

    courses = service.courses().list().execute().get("courses", [])
    for course in courses:
        print(f"Checking for new activity in course {course['name']}...")
        get_new_item(service, course, "announcements", last_check)
        get_new_item(service, course, "courseWork", last_check)
        get_new_item(service, course, "courseWorkMaterial", last_check)

# import aiohttp
# import asyncio
# from datetime import datetime, timezone
# from .appSettings import appSettings

# def parse_datetime(dt_str):
#     """Parse datetime string into a timezone-aware datetime object."""
#     try:
#         return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
#     except ValueError:
#         return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

# async def send_request(session, item_data):
#     """Send data asynchronously to the webhook endpoint."""
#     print("Sending Item Data:", item_data)
#     try:
#         async with session.post(
#             appSettings.webhook_url,
#             headers={"Content-Type": "application/json"},
#             json=item_data
#         ) as response:
#             print(f"Response Status: {response.status}, Content: {await response.text()}")
#     except aiohttp.ClientError as e:
#         print(f"Error sending data: {e}")

# async def get_new_item(session, service, course, item_type, last_check):
#     """Fetch new items (announcements, coursework, etc.) for a course and send them if they are new."""
#     print(f"Fetching {item_type} for course: {course['name']}")

#     try:
#         if item_type == "announcements":
#             items = service.courses().announcements().list(courseId=course["id"], orderBy="updateTime desc").execute()
#         elif item_type == "courseWork":
#             items = service.courses().courseWork().list(courseId=course["id"], orderBy="updateTime desc").execute()
#         elif item_type == "courseWorkMaterial":
#             items = service.courses().courseWorkMaterials().list(courseId=course["id"], orderBy="updateTime desc").execute()

#         print(f"Items fetched: {items}")

#         tasks = []
#         for item in items.get(item_type, []):
#             update_time = parse_datetime(item["updateTime"])
#             print(f"Item update time: {update_time}, Last check: {last_check}")

#             if update_time > last_check:
#                 print(f"New item found: {item}")
#                 is_new = (parse_datetime(item["creationTime"]) - update_time).total_seconds() < 300
#                 item_data = {
#                     "course": course,
#                     "activity": item,
#                     "type": item_type,
#                     "is_new": is_new
#                 }
#                 tasks.append(send_request(session, item_data))
#             else:
#                 break

#         await asyncio.gather(*tasks)

#     except Exception as e:
#         print(f"Error fetching {item_type} for course {course['name']}: {e}")

# async def notify_new_activity(service):
#     """Notify new activity across all courses asynchronously."""
#     print("Last check:", appSettings.last_check)
#     last_check = datetime.fromisoformat(appSettings.last_check).replace(tzinfo=timezone.utc) if appSettings.last_check else datetime.now(timezone.utc)
#     appSettings.update("last_check", datetime.now(timezone.utc).isoformat())

#     try:
#         courses = service.courses().list().execute().get("courses", [])
#         print(f"Found {len(courses)} courses")

#         async with aiohttp.ClientSession() as session:
#             tasks = []
#             for course in courses:
#                 print(f"Checking for new activity in course: {course['name']}...")

#                 tasks.append(get_new_item(session, service, course, "announcements", last_check))
#                 tasks.append(get_new_item(session, service, course, "courseWork", last_check))
#                 tasks.append(get_new_item(session, service, course, "courseWorkMaterial", last_check))

#             await asyncio.gather(*tasks)

#     except Exception as e:
#         print(f"Error notifying new activities: {e}")
