# -*- coding: utf-8 -*-
from tornado.template import Template
import handler


class Treatment(object):
    title = ''
    description = ''
    settings = dict()

    @staticmethod
    def content(settings):
        return ''


class Sessions(Treatment):
    title = 'Sessions'
    description = '分Session进行下一个阶段'
    settings = dict(sessions=[dict(des='', treatments=[]), ])

    @staticmethod
    def content(settings):
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
                                {% set t = handlers[treatment['code']] %}
                                <input type="hidden" form-domain="code" value="{{ t.__name__ }}">
                                <a href="javascript:void(0)" class="remove-treatment"><span class="glyphicon glyphicon-minus-sign" aria-hidden="true"></span></a>
                                <span class="treatment-title">{{ t.title }}</span>
                                <div class="treatment-content" form-domain="data">
                                    {% raw t.content(treatment) %}
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
        ''').generate(settings=settings, handlers=handler.hs.handlers)


class Repeat(Treatment):
    title = '重复'
    description = '其中的Treatment将会重复若干次'
    settings = dict(repeat=1, shuffle=False, treatments=[])

    @staticmethod
    def content(settings):
        return Template('''
            <div class="form-group">
                <label class="col-md-2 control-label">重复次数</label>
                <div class="col-md-4">
                    <input type="number" class="form-control" form-domain="repeat" value="{{ settings['repeat'] }}" required>
                </div>
            </div>
            <!-- <div class="form-group">
                <div class="col-md-4">
                    <div class="checkbox">
                        <label>
                          <input type="checkbox"  class="form-control" form-domain="shuffle"
                            {{ 'checked="checked"' if False else '' }} required> 是否重新分组
                        </label>
                    </div>
                </div>
            </div> -->
            <div class="treatments">

                {% for treatment in settings['treatments'] %}
                    <div class="well treatment" form-domain="[]treatments">
                        {% set t = handlers[treatment['code']] %}
                        <input type="hidden" form-domain="code" value="{{ t.__name__ }}">
                        <a href="javascript:void(0)" class="remove-treatment"><span class="glyphicon glyphicon-minus-sign" aria-hidden="true"></span></a>
                        <span class="treatment-title">{{ t.title }}</span>
                        <div class="treatment-content" form-domain="data">
                            {% raw t.content(treatment) %}
                        </div>
                    </div>
                {% end %}

            </div>
        ''').generate(settings=settings, handlers=handler.hs.handlers)