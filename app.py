# app.py
# GTD Web App - entry point
from flask import Flask, render_template, request, redirect, url_for
from datetime import date
import db


app = Flask(__name__)


# ---------- Home ----------
@app.route("/")
def home():
    return redirect(url_for("inbox"))


# ---------- INBOX: "Collect" phase ----------
@app.route("/inbox")
def inbox():
    items = db.fetch_all(
        "SELECT * FROM items WHERE status = 'inbox' ORDER BY created_at DESC"
    )
    return render_template("inbox.html", items=items, count=len(items))


@app.route("/inbox/add", methods=["POST"])
def inbox_add():
    """Stuff -> "IN" tray."""
    title = request.form.get("title", "").strip()
    notes = request.form.get("notes", "").strip()
    if title:  # ignore empty submissions
        db.execute(
            "INSERT INTO items (title, notes, status) VALUES (%s, %s, 'inbox')",
            (title, notes or None),
        )
    return redirect(url_for("inbox"))


@app.route("/inbox/trash/<int:item_id>", methods=["POST"])
def inbox_trash(item_id):
    """Workflow: Eliminate -> Trash (soft delete, keeps history)."""
    db.execute(
        "UPDATE items SET status = 'trash', updated_at = CURRENT_TIMESTAMP "
        "WHERE id = %s AND status = 'inbox'",
        (item_id,),
    )
    return redirect(url_for("inbox"))

# ---------- PROCESS: "What is it? Is it actionable?" ----------
@app.route("/process")
def process():
    """Show ONE inbox item at a time (oldest first) for processing."""
    item = db.fetch_one(
        "SELECT * FROM items WHERE status = 'inbox' "
        "ORDER BY created_at ASC LIMIT 1"
    )
    remaining = db.fetch_one(
        "SELECT COUNT(*) AS c FROM items WHERE status = 'inbox'"
    )
    count = remaining["c"] if remaining else 0
    contexts = db.fetch_all("SELECT * FROM contexts ORDER BY name")
    return render_template("process.html", item=item, count=count,
                           contexts=contexts)


def _move(item_id, new_status, extra_sql="", params=()):
    """Helper: move an item to a new status, then return to processing."""
    db.execute(
        "UPDATE items SET status = %s, updated_at = CURRENT_TIMESTAMP"
        + extra_sql + " WHERE id = %s",
        (new_status, *params, item_id),
    )
    return redirect(url_for("process"))


# --- NO branch: not actionable ---
@app.route("/process/<int:item_id>/trash", methods=["POST"])
def process_trash(item_id):
    return _move(item_id, "trash")


@app.route("/process/<int:item_id>/someday", methods=["POST"])
def process_someday(item_id):
    return _move(item_id, "someday_maybe")


@app.route("/process/<int:item_id>/reference", methods=["POST"])
def process_reference(item_id):
    return _move(item_id, "reference")


# --- YES branch: simple decisions ---
@app.route("/process/<int:item_id>/done", methods=["POST"])
def process_done(item_id):
    """'Do it' — takes less than 2 minutes."""
    return _move(item_id, "done", 
                 ", completed_at = CURRENT_TIMESTAMP")


@app.route("/process/<int:item_id>/next", methods=["POST"])
def process_next(item_id):
    """'Defer it' — as soon as I can -> Next Actions list (with context)."""
    context_id = request.form.get("context_id", type=int)
    if context_id:
        return _move(item_id, "next_action",
                     ", context_id = %s", (context_id,))
    return _move(item_id, "next_action")

# --- YES branch: decisions that need extra info ---
@app.route("/process/<int:item_id>/delegate", methods=["POST"])
def process_delegate(item_id):
    """'Delegate it' -> Waiting For (tracked on a person)."""
    who = request.form.get("delegated_to", "").strip() or "Unknown"
    return _move(item_id, "waiting_for",
                 ", delegated_to = %s", (who,))


@app.route("/process/<int:item_id>/schedule", methods=["POST"])
def process_schedule(item_id):
    """'Defer it' to a specific day/time -> Calendar."""
    due_date = request.form.get("due_date", "").strip() or None
    due_time = request.form.get("due_time", "").strip() or None
    return _move(item_id, "scheduled",
                 ", due_date = %s, due_time = %s", (due_date, due_time))


@app.route("/process/<int:item_id>/project", methods=["POST"])
def process_project(item_id):
    """Multi-step? -> Create Project; item becomes its first Next Action."""
    name = request.form.get("project_name", "").strip() or "Untitled Project"
    project = db.execute_returning(
        "INSERT INTO projects (name) VALUES (%s) RETURNING id",
        (name,),
    )
    return _move(item_id, "next_action",
                 ", project_id = %s", (project["id"],))

# ---------- LISTS: view items by status ----------
VALID_STATUSES = ["inbox", "next_action", "scheduled", "waiting_for",
                  "someday_maybe", "reference", "done", "trash"]

LIST_TITLES = {
    "next_action":  "➡ Next Actions",
    "scheduled":    "📅 Scheduled (Calendar)",
    "waiting_for":  "🤝 Waiting For",
    "someday_maybe": "☁ Someday / Maybe",
    "reference":    "📁 Reference",
    "done":         "✅ Completed",
    "trash":        "🗑 Trash",
}


@app.route("/list/<status>")
def list_view(status):
    if status not in VALID_STATUSES:
        return "Not found", 404
    context_id = request.args.get("context", type=int)
    contexts = db.fetch_all("SELECT * FROM contexts ORDER BY name")
    sql = ("SELECT i.*, p.name AS project_name, c.name AS context_name "
           "FROM items i "
           "LEFT JOIN projects p ON i.project_id = p.id "
           "LEFT JOIN contexts c ON i.context_id = c.id "
           "WHERE i.status = %s")
    params = [status]
    if context_id:
        sql += " AND i.context_id = %s"
        params.append(context_id)
    sql += " ORDER BY i.created_at DESC"
    items = db.fetch_all(sql, tuple(params))
    return render_template("list.html", items=items, status=status,
                           title=LIST_TITLES.get(status, status.title()),
                           contexts=contexts, active_context=context_id)


@app.route("/items/<int:item_id>/done", methods=["POST"])
def item_done(item_id):
    """Mark an item done from any list ('Do' phase)."""
    return _move(item_id, "done", ", completed_at = CURRENT_TIMESTAMP")


@app.route("/items/<int:item_id>/restore", methods=["POST"])
def item_restore(item_id):
    """Pull an item out of Trash back to Inbox."""
    return _move(item_id, "inbox")

@app.route("/items/<int:item_id>/set_context", methods=["POST"])
def item_set_context(item_id):
    """Assign/change a context from any list page."""
    context_id = request.form.get("context_id", type=int)
    db.execute(
        "UPDATE items SET context_id = %s, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = %s",
        (context_id, item_id),
    )
    return redirect(request.referrer or url_for("inbox"))


# ---------- REVIEW: weekly review dashboard ----------
@app.route("/review")
def review():
    today = date.today()

    # 1. Inbox still to process (get current = get clear)
    inbox_row = db.fetch_one(
        "SELECT COUNT(*) AS c FROM items WHERE status = 'inbox'")
    inbox_count = inbox_row["c"] if inbox_row else 0

    # 2. Calendar: scheduled items by date (overdue shown first)
    upcoming = db.fetch_all(
        "SELECT * FROM items WHERE status = 'scheduled' "
        "AND due_date IS NOT NULL ORDER BY due_date, due_time NULLS LAST")

    # 3. Stuck projects: active but NO open actions
    stuck = db.fetch_all(
        "SELECT p.* FROM projects p WHERE p.status = 'active' "
        "AND NOT EXISTS (SELECT 1 FROM items i WHERE i.project_id = p.id "
        "AND i.status IN ('next_action','scheduled','waiting_for'))")

    # 4. Stale next actions: untouched longest
    stale = db.fetch_all(
        "SELECT * FROM items WHERE status = 'next_action' "
        "ORDER BY updated_at ASC LIMIT 5")

    # 5. Waiting For: who owes you what
    waiting = db.fetch_all(
        "SELECT * FROM items WHERE status = 'waiting_for' "
        "ORDER BY created_at ASC")

    # 6. Overview counts of every list
    counts = db.fetch_all(
        "SELECT status, COUNT(*) AS c FROM items GROUP BY status")

    return render_template("review.html", today=today,
                           inbox_count=inbox_count, upcoming=upcoming,
                           stuck=stuck, stale=stale, waiting=waiting,
                           counts=counts, titles=LIST_TITLES)

# ---------- PROJECTS: "What's the successful outcome?" ----------
@app.route("/projects")
def projects_view():
    """All active projects, each with its next actions."""
    projects = db.fetch_all(
        "SELECT * FROM projects WHERE status = 'active' ORDER BY created_at DESC"
    )
    items = db.fetch_all(
        "SELECT * FROM items WHERE project_id IS NOT NULL "
        "AND status IN ('next_action','scheduled','waiting_for') "
        "ORDER BY created_at ASC"
    )
    by_project = {}
    for it in items:
        by_project.setdefault(it["project_id"], []).append(it)
    return render_template("projects.html",
                           projects=projects, items_by_project=by_project)


@app.route("/projects/add", methods=["POST"])
def project_add():
    name = request.form.get("name", "").strip()
    outcome = request.form.get("outcome", "").strip()
    if name:
        db.execute(
            "INSERT INTO projects (name, outcome) VALUES (%s, %s)",
            (name, outcome or None),
        )
    return redirect(url_for("projects_view"))


@app.route("/projects/<int:project_id>/complete", methods=["POST"])
def project_complete(project_id):
    db.execute(
        "UPDATE projects SET status = 'completed', "
        "completed_at = CURRENT_TIMESTAMP WHERE id = %s",
        (project_id,),
    )
    return redirect(url_for("projects_view"))


@app.route("/projects/<int:project_id>/add_action", methods=["POST"])
def project_add_action(project_id):
    """Planning: add the project's next action."""
    title = request.form.get("title", "").strip()
    if title:
        db.execute(
            "INSERT INTO items (title, status, project_id) "
            "VALUES (%s, 'next_action', %s)",
            (title, project_id),
        )
    return redirect(url_for("projects_view"))

# ---------- EDIT & MOVE: fix or relocate any item ----------
@app.route("/items/<int:item_id>/edit", methods=["GET"])
def item_edit(item_id):
    """Show the edit form for any item."""
    item = db.fetch_one("SELECT * FROM items WHERE id = %s", (item_id,))
    if not item:
        return "Not found", 404
    contexts = db.fetch_all("SELECT * FROM contexts ORDER BY name")
    projects = db.fetch_all(
        "SELECT * FROM projects WHERE status = 'active' ORDER BY name")
    return render_template("edit.html", item=item,
                           contexts=contexts, projects=projects)


@app.route("/items/<int:item_id>/edit", methods=["POST"])
def item_update(item_id):
    """Save edits: fields + move to another list."""
    title = request.form.get("title", "").strip()
    notes = request.form.get("notes", "").strip() or None
    status = request.form.get("status", "inbox")
    project_id = request.form.get("project_id", type=int)
    context_id = request.form.get("context_id", type=int)
    due_date = request.form.get("due_date", "").strip() or None
    due_time = request.form.get("due_time", "").strip() or None
    delegated_to = request.form.get("delegated_to", "").strip() or None

    # basic safety: need a title and a known status
    if not title or status not in VALID_STATUSES:
        return redirect(request.referrer or url_for("inbox"))

    if status == "done":
        db.execute(
            "UPDATE items SET title=%s, notes=%s, status=%s, project_id=%s, "
            "context_id=%s, due_date=%s, due_time=%s, delegated_to=%s, "
            "completed_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP "
            "WHERE id=%s",
            (title, notes, status, project_id, context_id, due_date,
             due_time, delegated_to, item_id))
    else:
        db.execute(
            "UPDATE items SET title=%s, notes=%s, status=%s, project_id=%s, "
            "context_id=%s, due_date=%s, due_time=%s, delegated_to=%s, "
            "completed_at=NULL, updated_at=CURRENT_TIMESTAMP "
            "WHERE id=%s",
            (title, notes, status, project_id, context_id, due_date,
             due_time, delegated_to, item_id))

    # land on the list the item now lives in
    return redirect(url_for("list_view", status=status))


@app.route("/trash/empty", methods=["POST"])
def trash_empty():
    """Permanently delete everything in Trash."""
    db.execute("DELETE FROM items WHERE status = 'trash'")
    return redirect(url_for("list_view", status="trash"))

if __name__ == "__main__":
    app.run(debug=True, port=955)