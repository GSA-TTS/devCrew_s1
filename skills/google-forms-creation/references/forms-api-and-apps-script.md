---
created: "2026-11-04T19:03:30Z"
updated: "2026-11-04T19:09:21Z"
---

# Forms API and Apps Script patterns

## Forms API (REST v1)

### Scopes

- Create or edit a form: one of `drive`, `drive.file` or `forms.body`.
  Prefer the least-privilege `forms.body` unless the user also needs Drive
  access. A full scope name is the short name appended to the https address
  www.googleapis.com/auth/ (for example, that address followed by
  `forms.body`).
- Read responses: `forms.responses.readonly`.
- Setup: a Google Cloud project with the Forms API enabled and OAuth
  authorization. For local use, Application Default Credentials work after
  `gcloud auth application-default login`.

```python
from google.auth import default
from googleapiclient.discovery import build

FORMS_BODY = "<full forms.body scope name>"  # see Scopes above
creds, _ = default(scopes=[FORMS_BODY])
forms = build("forms", "v1", credentials=creds)
```

### Create, then batchUpdate

`forms.create()` takes only a title; any other field in the request is
ignored. Add the description, questions and quiz mode afterwards with
`batchUpdate()`.

```python
created = forms.forms().create(body={"info": {"title": "Application form"}}).execute()
form_id = created["formId"]

forms.forms().batchUpdate(formId=form_id, body={"requests": [
    {"updateFormInfo": {
        "info": {"description": "Applications for open roles."},
        "updateMask": "description"}},
    {"createItem": {
        "item": {
            "title": "Role applied for",
            "questionItem": {"question": {
                "required": True,
                "choiceQuestion": {"type": "RADIO", "options": [
                    {"value": "Role A"}, {"value": "Role B"}]}}}},
        "location": {"index": 0}}}
]}).execute()
# Edit link: docs.google.com/forms/d/<form_id>/edit
```

### Question-type mapping for `createItem`

| Editor type | API question field |
|---|---|
| Multiple choice | `choiceQuestion`, `type: RADIO` |
| Checkboxes | `choiceQuestion`, `type: CHECKBOX` |
| Dropdown | `choiceQuestion`, `type: DROP_DOWN` |
| Short answer | `textQuestion` |
| Paragraph | `textQuestion` with `paragraph: true` |
| Linear scale | `scaleQuestion` |
| Date / Time | `dateQuestion` / `timeQuestion` |
| Section | a `pageBreakItem` item |

Every content change is one request in the `batchUpdate` list, so a loop over
rows of a CSV or sheet can append one `createItem` per row and send them in
batches; repeat per form to generate many forms.

### Quiz mode and grading

Turn the form into a quiz with `updateSettings`:

```python
forms.forms().batchUpdate(formId=form_id, body={"requests": [
    {"updateSettings": {
        "settings": {"quizSettings": {"isQuiz": True}},
        "updateMask": "quizSettings.isQuiz"}}
]}).execute()
```

Then give each scored question a `grading` block inside its `question`:

```python
"grading": {
    "pointValue": 1,
    "correctAnswers": {"answers": [{"value": "Mercury"}]},
    "whenRight": {"text": "Correct: Mercury orbits closest to the Sun."},
    "whenWrong": {"text": "Review: the innermost planet is Mercury."}
}
```

## Apps Script (FormApp)

Runs inside Google Workspace at script.google.com, with no external server or
credentials; suits building a form from a Sheet, also on a schedule.

```javascript
function buildForm() {
  const form = FormApp.create('Application form');
  form.setDescription('Applications for open roles.');
  form.addMultipleChoiceItem()
      .setTitle('Role applied for')
      .setChoiceValues(['Role A', 'Role B'])
      .setRequired(true);
  form.addParagraphTextItem().setTitle('Why are you interested in this role?');
  Logger.log(form.getEditUrl());
}
```

- Open existing forms with `FormApp.openById(id)` or `FormApp.openByUrl(url)`.
- Item classes: `MultipleChoiceItem`, `TextItem`, `ParagraphTextItem`,
  `CheckboxItem`, `ListItem` (dropdown), `ScaleItem`, `GridItem`, `DateItem`,
  `SectionHeaderItem`, `PageBreakItem` (sections).
- Quiz: `form.setIsQuiz(true)`, then set points and feedback on the choice
  items.
