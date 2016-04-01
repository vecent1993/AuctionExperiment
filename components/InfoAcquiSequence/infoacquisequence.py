# -*- coding: utf-8 -*-
"""
这个模块包含：含信息获取的序贯拍卖组件和相应用于参与人、主持人端的处理服务。
"""

from tornado.template import Template

import components.treatment
from ph import PlayerInfoAcquiSequence
from gh import GroupInfoAcquiSequence


class InfoAcquiSequence(components.treatment.PlayerGroup):
    title = '信息获取-序贯拍卖'
    description = '序贯拍卖前允许竞拍者购买后续信息'
    settings = dict(prob=0.333)

    @staticmethod
    def get_stage(settings, stage_code, cur_stage=None):
        stage_code_split = stage_code.split('-')
        if stage_code_split[1] == '0':
            return 'PlayerGroupWait', 'SessionHostMonitor', None, settings

        return 'PlayerInfoAcquiSequence', 'SessionHostMonitor', 'GroupInfoAcquiSequence', settings

    @staticmethod
    def content(settings):
        return Template('''
            <div class="form-group">
                <label class="col-md-2 control-label">高价值概率</label>
                <div class="col-md-4">
                    <input type="number" class="form-control" form-domain="prob"
                    value="{{ settings['prob'] }}" step="0.001" required>
                </div>
                <div class="checkbox col-md-4">
                    <label>
                        <input type="checkbox" form-domain="fixed"
                            {{ 'checked="checked"' if settings.get('fixed') else '' }}> 固定估价
                    </label>
                </div>
            </div>
        ''').generate(settings=settings)

    @staticmethod
    def player_result(db, expid, pid):
        results = db.query('select * from result_info_sequence where exp_id=%s and user_id=%s', expid, pid)
        return Template('''
        <table class="table table-hover" style="margin-bottom: 50px;">
            <thead>
            <tr>
                <th>#</th>
                <th>轮数</th>
                <th>阶段</th>
                <th>赢否</th>
                <th>获胜价</th>
                <th>成交价</th>
                <th>收益（点）</th>
            </tr>
            </thead>
            <tbody>
            {% for i, r in enumerate(results) %}
            <tr>
                <td>{{ i+1 }}</td>
                <td>{{ r['round'] }}</td>
                <td>{% if r['t'] == '0' %}信息获取拍卖
                    {% elif r['t'] == '1' %}A物品拍卖
                    {% else %}B物品拍卖
                    {% end %}
                </td>
                <td>{% if r['win'] == '0' %}否{% else %}赢{% end %}</td>
                <td>{{ r['win_price'] }}</td>
                <td>{{ r['win_pay'] }}</td>
                <td>{{ r['profit'] }}</td>
            </tr>
            {% end %}
            <tr class="success">
                <td colspan="6">合计</td>
                <td >{{ sum(map(lambda a: a['profit'], results)) }}</td>
            </tr>
            </tbody>
        </table>
        ''').generate(results=results)

    @staticmethod
    def get_data(db, expid):
        return db.query("""
                select * from info_sequence join user using(user_id) where exp_id=%s order by session,
                `group`, round, user_id
                """, expid)

    @staticmethod
    def host_result(db, expid):
        data = InfoAcquiSequence.get_data(db, expid)
        result = db.query("""
                select user_email, round, GROUP_CONCAT(profit order by t) as profits from result_info_sequence join user using(user_id)
                where exp_id=%s group by user_id, round;
                """, expid)
        return Template('''
        <h3>参与人收益：</h3>
        <table class="table table-hover" style="margin-bottom: 50px;">
            <thead>
            <tr>
                <th>#</th>
                <th>用户邮箱</th>
                <th>轮数</th>
                <th>信息拍卖收益</th>
                <th>A物品拍卖收益</th>
                <th>B物品拍卖收益</th>
                <th>本轮收益</th>
            </tr>
            </thead>
            <tbody>
            {% for i, r in enumerate(result) %}
            <tr>
                <td>{{ i+1 }}</td>
                <td>{{ r['user_email'] }}</td>
                <td>{{ r['round'] }}</td>
                {% set profits = map(float, r['profits'].split(',')) %}
                <td>{{ profits[0] if len(profits) >= 1 else '' }}</td>
                <td>{{ profits[1] if len(profits) >= 2 else '' }}</td>
                <td>{{ profits[2] if len(profits) >= 3 else '' }}</td>
                <td>{{ sum(profits) }}</td>
            </tr>
            {% end %}
            </tbody>
        </table>
        <h3>实验数据：</h3>
        <table class="table table-hover" style="margin-bottom: 50px;">
            <thead>
            <tr>
                <th>#</th>
                <th>用户名</th>
                <th>用户邮箱</th>
                <th>session</th>
                <th>group</th>
                <th>轮数</th>
                <th>A物品估价</th>
                <th>B物品估价</th>
                <th>信息报价</th>
                <th>A物品报价</th>
                <th>B物品报价</th>
            </tr>
            </thead>
            <tbody>
            {% for i, r in enumerate(data) %}
            <tr>
                <td>{{ i+1 }}</td>
                <td>{{ r['user_name'] }}</td>
                <td>{{ r['user_email'] }}</td>
                <td>{{ r['session'] }}</td>
                <td>{{ r['group'] }}</td>
                <td>{{ r['round'] }}</td>
                <td>{{ r['aq'] }}</td>
                <td>{{ r['bq'] }}</td>
                <td>{{ r['info_bid'] }}</td>
                <td>{{ r['a_bid'] }}</td>
                <td>{{ r['b_bid'] }}</td>
            </tr>
            {% end %}
            </tbody>
        </table>
        ''').generate(data=data, result=result)