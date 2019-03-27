import functools

from django.forms.formsets import DELETION_FIELD_NAME, ORDERING_FIELD_NAME

from wagtail.admin.edit_handlers import EditHandler, MultiFieldPanel

class InlinePanelForForeignKey ( EditHandler ):
    '''An InlinePanel that does not require a ParentalKey.'''

    def __init__ (
            self, modelandfield,
            exclude = None, panels = None, heading = '', label = '',
            min_num = None, max_num = None, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.panels = panels
        self.heading = heading or label
        self.label = label
        self.min_num = min_num
        self.max_num = max_num

        self.exclude = exclude
        self.modelandfield = modelandfield
#        self.key = key

    def clone(self):
        return InlinePanelForForeignKey(
            self.modelandfield,
            **self.clone_kwargs()
        )

    
    def clone_kwargs(self):
        #kwargs = super().clone_kwargs()
        kwargs = {}
        kwargs.update(
#            modelandfield = self.modelandfield,
            panels = self.panels,
            label = self.label,
            min_num = self.min_num,
            max_num = self.max_num,
            exclude = self.exclude,

#            key = self.key
        )

        print(kwargs)
        return kwargs

    def get_panel_definitions(self):
        if self.panels is not None:
            return self.panels
        # Failing that, get it from the model
        return extract_panel_definitions_from_model_class(
            self.db_field.related_model,
            exclude=[self.db_field.field.name]
        )

    def get_child_edit_handler(self):
        panels = self.get_panel_definitions()
        child_edit_handler = MultiFieldPanel(panels, heading=self.heading)
        return child_edit_handler.bind_to_model(self.db_field.related_model)

    def required_formsets(self):
        child_edit_handler = self.get_child_edit_handler()
        return {
            self.modelandfield: {
                'fields': child_edit_handler.required_fields(),
                'widgets': child_edit_handler.widget_overrides(),
                'min_num': self.min_num,
                'validate_min': self.min_num is not None,
                'max_num': self.max_num,
                'validate_max': self.max_num is not None
            }
        }

    def html_declarations(self):
        return self.get_child_edit_handler().html_declarations()

    def get_comparison(self):
        field_comparisons = []

        for panel in self.get_panel_definitions():
            field_comparisons.extend(
                panel.bind_to_model(self.db_field.related_model)
                .get_comparison())

        return [functools.partial(compare.ChildRelationComparison, self.db_field, field_comparisons)]

    def on_model_bound(self):
#        manager = getattr(self.model, self.relation_name)
#        self.db_field = manager.rel
        pass
    def on_instance_bound(self):
        self.formset = self.form.formsets[self.relation_name]

        self.children = []
        for subform in self.formset.forms:
            # override the DELETE field to have a hidden input
            subform.fields[DELETION_FIELD_NAME].widget = forms.HiddenInput()

            # ditto for the ORDER field, if present
            if self.formset.can_order:
                subform.fields[ORDERING_FIELD_NAME].widget = forms.HiddenInput()

            child_edit_handler = self.get_child_edit_handler()
            self.children.append(
                child_edit_handler.bind_to_instance(instance=subform.instance,
                                                    form=subform,
                                                    request=self.request))

        # if this formset is valid, it may have been re-ordered; respect that
        # in case the parent form errored and we need to re-render
        if self.formset.can_order and self.formset.is_valid():
            self.children.sort(
                key=lambda child: child.form.cleaned_data[ORDERING_FIELD_NAME] or 1)

        empty_form = self.formset.empty_form
        empty_form.fields[DELETION_FIELD_NAME].widget = forms.HiddenInput()
        if self.formset.can_order:
            empty_form.fields[ORDERING_FIELD_NAME].widget = forms.HiddenInput()

        self.empty_child = self.get_child_edit_handler()
        self.empty_child = self.empty_child.bind_to_instance(
            instance=empty_form.instance, form=empty_form, request=self.request)

    template = "wagtailadmin/edit_handlers/inline_panel.html"

    def render(self):
        formset = render_to_string(self.template, {
            'self': self,
            'can_order': self.formset.can_order,
        })
        js = self.render_js_init()
        return widget_with_script(formset, js)

    js_template = "wagtailadmin/edit_handlers/inline_panel.js"

    def render_js_init(self):
        return mark_safe(render_to_string(self.js_template, {
            'self': self,
            'can_order': self.formset.can_order,
        }))


