from bs4 import Tag


def base_form_test(form: Tag, action_url: str) -> None:

    assert form["method"] == "POST"
    assert action_url in form["action"]

    csrf_field = form.find("input", id="csrf_token")
    csrf_attr = csrf_field.attrs
    assert csrf_attr["type"] == "hidden"
    assert csrf_attr["name"] == "csrf_token"
    assert bool(csrf_attr["value"].strip())

    submit_button = form.find("button", id="submit")

    assert submit_button is not None
