# -*- coding: utf-8 -*-
from treatment import Treatment
from tornado.template import Template
from . import getTreatment


class Sessions(Treatment):
    def __init__(self, settings=None):
        super(Sessions, self).__init__(Sessions.__name__, 'Sessions', '分Session进行下一个阶段', settings)

    @property
    def content(self):
        if not self['settings']:
            self['settings'] = dict(code="Sessions", sessions=[dict(des='', treatments=[]), ])
        return Template('''
        <div role="tabpanel">

            <ul class="nav nav-tabs tab-presentation-list" role="tablist" class="">

                {% for i, _ in enumerate(settings['sessions']) %}
                <li role="presentation" class="{% if i == 0 %}active{% end %}">
                    <a href="#{{ i }}" aria-controls="{{ i }}" role="tab" data-toggle="tab">
                        <span class="session-id">session</span>
                    </a>
                </li>
                {% end %}

                <li role="presentation" class="add-session-presentation">
                    <a href="javascript:void(0)" aria-controls="" role="tab" data-toggle="tab">
                        <span class="session-id">*</span>
                    </a>
                </li>
            </ul>

            <div class="tab-content session-list">

                {% for i, session in enumerate(settings['sessions']) %}
                <div role="tabpanel" class="tab-pane session {% if i == 0 %}active{% end %}" id="{{ i }}" form-domain="[]sessions">
                    <br/>
                    <div class="form-group">
                        <label class="col-md-2 control-label">session名称</label>
                        <div class="col-md-8"><input class="form-control" type="text" form-domain="des" value="{{ session['des'] }}"></div>
                    </div>

                    <div class="treatments">

                        {% for treatment in session['treatments'] %}
                            <div class="well treatment" form-domain="[]treatments">
                                {% set t = getTreatment(treatment['code'])(treatment) %}
                                <input type="hidden" form-domain="code" value="{{ treatment['code'] }}">
                                <a href="javascript:void(0)" class="remove-treatment"><span class="glyphicon glyphicon-minus-sign" aria-hidden="true"></span></a>
                                <span class="treatment-title">{{ t['title'] }}</span>
                                <div class="treatment-content" form-domain="data">
                                    {% raw t.content %}
                                </div>
                            </div>
                        {% end %}

                    </div>
                </div>
                {% end %}

                <div role="tabpanel" class="tab-pane session empty" id="" form-domain="[]sessions">
                    <br/>
                    <div class="form-group">
                        <label class="col-md-2 control-label">session名称</label>
                        <div class="col-md-8"><input class="form-control" type="text" form-domain="des"></div>
                    </div>

                    <div class="treatments">

                    </div>
                </div>

            </div>

        </div>
        ''').generate(settings=self['settings'], getTreatment=getTreatment)
