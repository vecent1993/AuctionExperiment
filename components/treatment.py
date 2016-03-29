# -*- coding: utf-8 -*-
from tornado.template import Template

import components


class Treatment(object):
    title = ''
    description = ''
    settings = dict()

    @staticmethod
    def get_stage(settings, stage_code, cur_stage=None):
        return None, None, None, settings

    @staticmethod
    def content(settings):
        return ''

    @staticmethod
    def player_result(db, expid, pid):
        return ''

    @staticmethod
    def host_result(db, expid):
        return ''


class PlayerOnly(Treatment):
    @staticmethod
    def next_stage_code(settings, stage_code=None, round_=0):
        if len(stage_code.split('-')) == 1:
            return stage_code + '-1', round_
        else:
            return None


class PlayerGroup(Treatment):
    @staticmethod
    def next_stage_code(settings, stage_code=None, round_=0):
        stage_code_split = stage_code.split('-')
        if len(stage_code_split) == 1:
            return ('%s-0' % stage_code_split[0]), round_
        elif stage_code_split[1] == '0':
            return ('%s-1' % stage_code_split[0]), round_ + 1
        else:
            return None


class Container(Treatment):
    pass


class Train(Treatment):
    @staticmethod
    def get_stage(*args, **kwargs):
        return None


class Sessions(Container):
    title = 'Sessions'
    description = '分Session进行下一个阶段'
    settings = dict(sessions=[dict(des='', treatments=[]), ])

    @staticmethod
    def get_stage(settings, stage_code, cur_stage=None):
        stage_code_split = stage_code.split(':')
        if len(stage_code_split) == 1:
            return 'PlayerSessionWait', 'HostShuffle', None, settings
        else:
            cur = int(stage_code_split[1].split('-')[0])
            treatment_code = settings['sessions'][0]['treatments'][cur]['code']
            treatment = components.hub.treatments[treatment_code]
            return treatment.get_stage(settings['sessions'][0]['treatments'][cur],
                                       ':'.join(stage_code_split[1:]), cur_stage)

    @staticmethod
    def next_stage_code(settings, stage_code=None, round_=0):
        stage_code_split = stage_code.split(':')
        cur_stage_code = stage_code_split[0]
        if len(stage_code_split) == 1:
            if len(cur_stage_code.split('-')) == 1:  # '0' -> '0-1'
                return cur_stage_code + '-1', round_
            else:  # '0-1' -> '0-1:0'
                treatment_code = settings['sessions'][0]['treatments'][0]['code']
                treatment = components.hub.treatments[treatment_code]
                sub_stage_code = treatment.next_stage_code(settings['sessions'][0]['treatments'][0], '0', round_)
                return '%s:%s' % (cur_stage_code, sub_stage_code[0]), sub_stage_code[1]
        else:
            cur = int(stage_code_split[1].split('-')[0])
            if cur >= len(settings['sessions'][0]['treatments']):
                return None
            treatment_code = settings['sessions'][0]['treatments'][cur]['code']
            treatment = components.hub.treatments[treatment_code]
            sub_stage_code = treatment.next_stage_code(settings['sessions'][0]['treatments'][cur],
                                                  ':'.join(stage_code_split[1:]), round_)
            if not sub_stage_code:
                return Sessions.next_stage_code(settings, '%s:%s' % (cur_stage_code, cur+1), round_)
            else:
                return '%s:%s' % (cur_stage_code, sub_stage_code[0]), sub_stage_code[1]

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
                        <label class="col-md-2 control-label">名称</label>
                        <div class="col-md-3">
                            <input class="form-control" type="text" form-domain="des" value="{{ session['des'] }}">
                        </div>
                        <label class="col-md-2 control-label">比例</label>
                        <div class="col-md-2">
                            <input class="form-control" type="number" form-domain="ratio" value="{{ session.get('ratio', 100) }}">
                        </div>
                    </div>

                    <div class="treatments">

                        {% for treatment in session['treatments'] %}
                            <div class="well treatment" form-domain="[]treatments">
                                {% set t = treatments[treatment['code']] %}
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
                        <label class="col-md-2 control-label">名称</label>
                        <div class="col-md-3">
                            <input class="form-control" type="text" form-domain="des"">
                        </div>
                        <label class="col-md-2 control-label">比例</label>
                        <div class="col-md-2">
                            <input class="form-control" type="number" form-domain="ratio" value="100">
                        </div>
                    </div>

                    <div class="treatments">

                    </div>
                </div>

            </div>

        </div>
        ''').generate(settings=settings, treatments=components.hub.treatments)


class Repeat(Container):
    title = '重复'
    description = '其中的Treatment将会重复若干次'
    settings = dict(repeat=1, shuffle=False, treatments=[])

    @staticmethod
    def get_stage(settings, stage_code, cur_stage=None):
        stage_code_split = stage_code.split(':')
        if len(stage_code_split) == 1:
            if settings.get('auto'):
                return 'PlayerShuffleWait', 'AutoHostShuffle', None, settings
            return 'PlayerShuffleWait', 'HostShuffle', None, settings
        else:
            cur = int(stage_code_split[1].split('-')[0])
            treatment_code = settings['treatments'][cur]['code']
            treatment = components.hub.treatments[treatment_code]
            return treatment.get_stage(settings['treatments'][cur], ':'.join(stage_code_split[1:]), cur_stage)

    @staticmethod
    def next_stage_code(settings, stage_code=None, round_=0):
        stage_code_split = stage_code.split(':')
        cur_stage_code = stage_code_split[0]
        if len(stage_code_split) == 1:
            if len(cur_stage_code.split('-')) == 1:  # '0' -> '0-1'
                if settings.get('shuffle'):
                    return cur_stage_code + '-1', round_
                else:
                    return Repeat.next_stage_code(settings, cur_stage_code + '-1', round_)
            else:  # '0-1' -> '0-1:0'
                treatment_code = settings['treatments'][0]['code']
                treatment = components.hub.treatments[treatment_code]
                sub_stage_code = treatment.next_stage_code(settings['treatments'][0], '0', round_)
                return '%s:%s' % (cur_stage_code, sub_stage_code[0]), sub_stage_code[1]
        else:
            cur = int(stage_code_split[1].split('-')[0])
            if cur >= len(settings['treatments']):
                repeats = int(cur_stage_code.split('-')[1])
                if repeats >= int(settings['repeat']):
                    return None
                else:
                    if settings.get('shuffle'):
                        return '%s-%s' % (cur_stage_code.split('-')[0], repeats+1), round_
                    else:
                        return Repeat.next_stage_code(settings, '%s-%s' % (cur_stage_code.split('-')[0],
                                                                           repeats+1), round_)
            treatment_code = settings['treatments'][cur]['code']
            treatment = components.hub.treatments[treatment_code]
            sub_stage_code = treatment.next_stage_code(settings['treatments'][cur],
                                                       ':'.join(stage_code_split[1:]), round_)
            if not sub_stage_code:
                return Repeat.next_stage_code(settings, '%s:%s' % (cur_stage_code,cur+1), round_)
            else:
                return '%s:%s' % (cur_stage_code, sub_stage_code[0]), sub_stage_code[1]

    @staticmethod
    def content(settings):
        return Template('''
            <div class="form-group repeat">
                <label class="col-md-3 control-label">重复次数</label>
                <div class="col-md-2">
                    <input type="number" class="form-control" form-domain="repeat" value="{{ settings['repeat'] }}" required>
                </div>
                <div class="checkbox col-md-4">
                    <label>
                        <input type="checkbox" form-domain="shuffle"
                            {{ 'checked="checked"' if settings.get('shuffle') else '' }}> 是否重新分组
                    </label>
                </div>
            </div>
            <div class="form-group">
                <label class="col-md-3 control-label">每组人数</label>
                <div class="col-md-2">
                    <input class="form-control" type="number" form-domain="gplayers" value="{{ settings.get('gplayers', 2) }}">
                </div>
                <div class="checkbox col-md-4">
                    <label>
                        <input type="checkbox" form-domain="auto"
                            {{ 'checked="checked"' if settings.get('auto') else '' }}> 自动分组
                    </label>
                </div>

            </div>

            <div class="treatments">

                {% for treatment in settings['treatments'] %}
                    <div class="well treatment" form-domain="[]treatments">
                        {% set t = treatments[treatment['code']] %}
                        <input type="hidden" form-domain="code" value="{{ t.__name__ }}">
                        <a href="javascript:void(0)" class="remove-treatment"><span class="glyphicon glyphicon-minus-sign" aria-hidden="true"></span></a>
                        <span class="treatment-title">{{ t.title }}</span>
                        <div class="treatment-content" form-domain="data">
                            {% raw t.content(treatment) %}
                        </div>
                    </div>
                {% end %}

            </div>
        ''').generate(settings=settings, treatments=components.hub.treatments)