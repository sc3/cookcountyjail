// Summary model
var RowSummaryModel = Backbone.Model.extend({
    url: '/data/rows' 
});

// Summary view
var RowSummaryView = Backbone.View.extend({
    model: RowSummaryModel,
    el: '#rows',
    template: '#rows-summary',
    initialize: function(options) {
        this.template = (options.template) ? _.template(options.template) : _.template($(this.template).html());
        this.render();
        this.model.bind('reset', this.render, this);
    },
    render: function(options) {
        this.$el.html(this.template(this.model.toJSON()));
        return this;
    }
});

