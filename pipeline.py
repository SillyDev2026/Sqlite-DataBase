HALT = object()

class Pipeline:
    def __init__(self):
        self.stages = []
        self.context = {}

        self.before_stage = None
        self.after_stage = None

        self.merge_fn = None
        self.catch_fn = None
        self.finally_fn = None

    def step(self, fn, label=None):
        self.stages.append({
            "type": "step",
            "fn": fn,
            "label": label
        })
        return self

    def parallel(self, fns, label=None):
        self.stages.append({
            "type": "parallel",
            "fns": fns,
            "label": label
        })
        return self

    def branch(self, cond_fn, branches, label=None):
        self.stages.append({
            "type": "branch",
            "condition_fn": cond_fn,
            "branches": branches,
            "label": label
        })
        return self

    def filter(self, fn, label=None):
        self.stages.append({
            "type": "filter",
            "fn": fn,
            "label": label
        })
        return self

    def repeat(self, stage_fn, cond_fn, label=None):
        self.stages.append({
            "type": "repeat",
            "stage_fn": stage_fn,
            "condition_fn": cond_fn,
            "label": label
        })
        return self

    def merge(self, fn):
        self.merge_fn = fn
        return self

    def catch(self, fn):
        self.catch_fn = fn
        return self

    def finally_(self, fn):
        self.finally_fn = fn
        return self

    def hooks(self, before=None, after=None):
        self.before_stage = before
        self.after_stage = after
        return self

    def run(self, input_value):
        result = input_value
        ctx = self.context

        try:
            for stage in self.stages:
                label = stage.get("label", stage["type"])

                if self.before_stage:
                    self.before_stage(label, result, ctx)

                stage_type = stage["type"]

                # STEP
                if stage_type == "step":
                    result = stage["fn"](result, ctx)

                # PARALLEL
                elif stage_type == "parallel":
                    results = [
                        fn(result, ctx)
                        for fn in stage["fns"]
                    ]

                    if self.merge_fn:
                        result = self.merge_fn(results, ctx)
                    else:
                        result = results

                # BRANCH
                elif stage_type == "branch":
                    key = stage["condition_fn"](result, ctx)
                    branch = stage["branches"].get(
                        key,
                        stage["branches"].get("other")
                    )

                    if branch:
                        result, _ = branch.run(result)

                # FILTER
                elif stage_type == "filter":
                    if not stage["fn"](result, ctx):
                        result = HALT

                # REPEAT
                elif stage_type == "repeat":
                    while stage["condition_fn"](result, ctx):
                        result = stage["stage_fn"](result, ctx)

                if self.after_stage:
                    self.after_stage(label, result, ctx)

                if result is HALT:
                    break

        except Exception as e:
            if self.catch_fn:
                return self.catch_fn(e, ctx), ctx
            raise

        finally:
            if self.finally_fn:
                self.finally_fn(result, ctx)

        return result, ctx
