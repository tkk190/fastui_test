from datetime import date
from io import BytesIO

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastui import FastUI, AnyComponent, prebuilt_html, components as c
from fastui.components.display import DisplayMode, DisplayLookup
from fastui.events import GoToEvent, BackEvent, PageEvent
from pydantic import BaseModel, Field
import xlsxwriter
from starlette.responses import StreamingResponse

app = FastAPI()


class User(BaseModel):
    id: int
    name: str
    dob: date = Field(title='Date of Birth')
    hair_color: str

# define some users
users = [
    User(id=1, name='John', dob=date(1990, 1, 1), hair_color='blond'),
    User(id=2, name='Jack', dob=date(1991, 1, 1), hair_color='black'),
    User(id=3, name='Jill', dob=date(1992, 1, 1), hair_color='red'),
    User(id=4, name='Jane', dob=date(1993, 1, 1), hair_color='brown'),
]

stmt = """
    select u.abc, u.cd 
    from user u 
    inner join group g on g.abd = u.abc 
    where g.a = 'Hello World'
"""

@app.get("/api/", response_model=FastUI, response_model_exclude_none=True)
def users_table() -> list[AnyComponent]:
    return [
        c.Page(  # Page provides a basic container for components
            components=[
                c.Heading(text='Users', level=2),  # renders `<h2>Users</h2>`
                c.Table[User](  # c.Table is a generic component parameterized with the model used for rows
                    data=users,
                    # define two columns for the table
                    columns=[
                        # the first is the users, name rendered as a link to their profile
                        DisplayLookup(field='name', on_click=GoToEvent(url='/user/{id}/')),
                        # the second is the date of birth, rendered as a date
                        DisplayLookup(field='dob', mode=DisplayMode.date),
                    ],
                ),
                c.Link(
                    on_click=GoToEvent(url='excel'),
                    components=[c.Text(text='Create Excel File')]
                ),
                c.Heading(text='Statement', level=3),  # renders `<h2>Users</h2>`
                c.Code(
                    text=stmt,
                    language='sql'
                ),
            ]
        ),
    ]


@app.get("/api/user/{user_id}/", response_model=FastUI, response_model_exclude_none=True)
def user_profile(user_id: int) -> list[AnyComponent]:
    """
    User profile page, the frontend will fetch this when the user visits `/user/{id}/`.
    """
    try:
        user = next(u for u in users if u.id == user_id)
    except StopIteration:
        raise HTTPException(status_code=404, detail="User not found")
    return [
        c.Page(
            components=[
                c.Heading(text=user.name, level=2),
                c.Link(components=[c.Text(text='Back')], on_click=BackEvent()),
                c.Details(data=user),
            ]
        ),
    ]

@app.get("/excel", response_description='xlsx')
def users_table():
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()
    for row, user in enumerate([u.model_dump(mode='json') for u in users]):
        if row == 0:
            for col, key in enumerate(user.keys()):
                worksheet.write(0, col, key)
        for col, item in enumerate(user.values()):
            worksheet.write(row + 1, col, item)
    workbook.close()
    output.seek(0)

    headers = {
        'Content-Disposition': 'attachment; filename="report.xlsx"'
    }

    return StreamingResponse(output, headers=headers)

@app.get('/{path:path}')
async def html_landing() -> HTMLResponse:
    """Simple HTML page which serves the React app, comes last as it matches all paths."""
    return HTMLResponse(prebuilt_html(title='FastUI Demo'))


