import json
import time

import gradio as gr

import scripts.mo.ui_navigation as nav
import scripts.mo.ui_styled_html as styled
from scripts.mo.dl.download_manager import DownloadManager, RECORD_STATUS_ERROR, RECORD_STATUS_EXISTS, \
    RECORD_STATUS_COMPLETED, GENERAL_STATUS_COMPLETED, GENERAL_STATUS_ERROR, GENERAL_STATUS_CANCELLED, \
    GENERAL_STATUS_IN_PROGRESS
from scripts.mo.environment import env, logger

_STATE_PENDING = 'Pending'
_STATE_IN_PROGRESS = 'In Progress'
_STATE_COMPLETED = 'Completed'
_STATE_EXISTS = 'Exists'
_STATE_ERROR = 'Error'


def _format_percentage(part, total):
    return int((part / total) * 100)


def _format_bytes(bytes_to_format):
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    while bytes_to_format >= 1000 and i < len(units) - 1:
        bytes_to_format /= 1000
        i += 1
    return f"{bytes_to_format:.2f} {units[i]}"


def _format_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
    else:
        return f"{int(m):02d}:{int(s):02d}"


def _format_download_speed(speed):
    if speed is None:
        return 'Undefined'

    units = ['B/s', 'KB/s', 'MB/s', 'GB/s', 'TB/s']
    unit_index = 0

    while speed >= 1000 and unit_index < len(units) - 1:
        speed /= 1000.0
        unit_index += 1

    return '{:.2f}{}'.format(speed, units[unit_index])


def _build_progress_update(record_id, state=None, result_text=None, result_title=None, progress_info_left=None,
                           progress_info_center=None, progress_info_right=None, progress_preview_info_left=None,
                           progress_preview_info_center=None, progress_preview_info_right=None, progress=None,
                           progress_preview=None) -> str:
    update = {'id': record_id}

    if state is not None:
        update['state'] = state

    if result_text is not None:
        update['result_text'] = result_text

    if result_title is not None:
        update['result_title'] = result_title

    if progress_info_left is not None:
        update['progress_info_left'] = progress_info_left

    if progress_info_center is not None:
        update['progress_info_center'] = progress_info_center

    if progress_info_right is not None:
        update['progress_info_right'] = progress_info_right

    if progress_preview_info_left is not None:
        update['progress_preview_info_left'] = progress_preview_info_left

    if progress_preview_info_center is not None:
        update['progress_preview_info_center'] = progress_preview_info_center

    if progress_preview_info_right is not None:
        update['progress_preview_info_right'] = progress_preview_info_right

    if progress is not None:
        update['progress'] = progress

    if progress_preview is not None:
        update['progress_preview'] = progress_preview

    return json.dumps(update)


def _build_update(progress_update=None, status_message=None, is_start_button_visible=None,
                  is_cancel_button_visible=None,
                  is_back_button_visible=None):
    upd = [
        gr.HTML.update() if status_message is None else gr.HTML.update(value=status_message, visible=True),
        gr.Button.update() if is_start_button_visible is None else gr.Button.update(visible=is_start_button_visible),
        gr.Button.update() if is_cancel_button_visible is None else gr.Button.update(visible=is_cancel_button_visible),
        gr.Button.update() if is_back_button_visible is None else gr.Button.update(visible=is_back_button_visible),
        gr.Textbox.update() if progress_update is None else gr.Textbox.update(value=progress_update)
    ]
    return upd


def _generate_info_center(bytes_ready, bytes_total):
    if isinstance(bytes_ready, int) and isinstance(bytes_total, int) and bytes_total > 0:
        return f"{_format_bytes(bytes_ready)} / {_format_bytes(bytes_total)}"
    else:
        if isinstance(bytes_ready, int):
            return _format_bytes(bytes_ready)
    return ''


def _generate_progress(bytes_ready, bytes_total):
    if isinstance(bytes_ready, int) and isinstance(bytes_total, int) and bytes_total > 0:
        return _format_percentage(bytes_ready, bytes_total)
    else:
        return 0


def _generate_info_right(speed_rate, elapsed):
    speed = _format_download_speed(speed_rate) if isinstance(speed_rate, float) and speed_rate > 0 else ''
    elapsed = '' if not isinstance(elapsed, float) or elapsed == 0 else _format_time(elapsed)
    right_info = ''
    if speed:
        right_info += speed
    if speed and elapsed:
        right_info += ' | '
    if elapsed:
        right_info += elapsed

    return right_info


def _generate_js_record_update(record_id, update):
    result = {'id': record_id}

    status = update.get('status')
    if status is not None:
        result['status'] = status

    if status is not None:
        if status == RECORD_STATUS_EXISTS:
            result['result_title'] = 'File already exists.'
            if update.get('destination') is not None:
                result['result_text'] = update['destination']

        elif status == RECORD_STATUS_COMPLETED:
            result['result_title'] = 'Download completed.'
            result_text = ''

            if update.get('destination') is not None:
                result_text += update['destination']

            if update.get('preview_destination'):
                result_text += '<br>' if len(result_text) > 0 else ''
                result_text += update['preview_destination']

            if len(result_text) > 0:
                result['result_text'] = result_text

        elif status == RECORD_STATUS_ERROR:
            result['result_title'] = 'Download failed.'
            if update.get('exception') is not None:
                result['result_text'] = update['exception']

    if update.get('filename') is not None:
        result['progress_info_left'] = update['filename']

    if update.get('dl') is not None:
        dl = update['dl']
        result['progress_info_center'] = _generate_info_center(dl['bytes_ready'], dl['bytes_total'])
        result['progress_info_right'] = _generate_info_right(dl['speed_rate'], dl['elapsed'])
        result['progress'] = _generate_progress(dl['bytes_ready'], dl['bytes_total'])

    if update.get('preview_dl') is not None:
        dl = update['preview_dl']
        result['progress_preview_info_center'] = _generate_info_center(dl['bytes_ready'], dl['bytes_total'])
        result['progress_preview_info_right'] = _generate_info_right(dl['speed_rate'], dl['elapsed'])
        result['progress_preview'] = _generate_progress(dl['bytes_ready'], dl['bytes_total'])

    return result

    # {
    #   "general_status": "Completed",
    #   "records": {
    #     "20": {
    #       "status": "Completed",
    #       "filename": "yaeMikoRealistic_yaemikoMixed.safetensors",
    #       "destination": "/Users/alexander/Projects/Python/mo_files/models/VAE/yaeMikoRealistic_yaemikoMixed.safetensors",
    #       "dl": {
    #         "bytes_ready": 61134280,
    #         "bytes_total": 61134280,
    #         "speed_rate": 0,
    #         "elapsed": 0
    #       },
    #       "preview_filename": "yaeMikoRealistic_yaemikoMixed.safetensors",
    #       "preview_destination": "/Users/alexander/Projects/Python/mo_files/models/VAE/yaeMikoRealistic_yaemikoMixed.safetensors",
    #       "preview_dl": {
    #         "bytes_ready": 0,
    #         "bytes_total": 0,
    #         "speed_rate": 0,
    #         "elapsed": 0
    #       }
    #     }
    #   }
    # }
    pass


def _generate_js_general_update(update):
    status_message = ''
    if update.get('general_status') is not None:
        if update['general_status'] == GENERAL_STATUS_IN_PROGRESS:
            status_message = styled.alert_primary('Download in progress.')
        elif update['general_status'] == GENERAL_STATUS_COMPLETED:
            status_message = styled.alert_success('Download completed.')
        elif update['general_status'] == GENERAL_STATUS_CANCELLED:
            status_message = styled.alert_warning('Download cancelled')
        elif update['general_status'] == GENERAL_STATUS_ERROR:
            stat = ['Download failed.']
            if update.get('exception') is not None:
                stat.append(update['exception'])
            status_message = styled.alert_danger(stat)

    js_result = {}
    if update.get('records') is not None:
        upd_list = []
        for record_id, upd in update['records'].items():
            upd_list.append(_generate_js_record_update(record_id, upd))
        js_result['records'] = upd_list

    #   TODO make other updates
    return json.dumps(js_result)


def _on_start_click(records):
    yield _build_update(
        status_message=styled.alert_primary('Download in progress.'),
        is_start_button_visible=False,
        is_cancel_button_visible=True,
        is_back_button_visible=False,
    )

    # {
    #   "general_status": "Completed",
    #   "records": {
    #     "20": {
    #       "status": "Completed",
    #       "filename": "yaeMikoRealistic_yaemikoMixed.safetensors",
    #       "destination": "/Users/alexander/Projects/Python/mo_files/models/VAE/yaeMikoRealistic_yaemikoMixed.safetensors",
    #       "dl": {
    #         "bytes_ready": 61134280,
    #         "bytes_total": 61134280,
    #         "speed_rate": 0,
    #         "elapsed": 0
    #       },
    #       "preview_filename": "yaeMikoRealistic_yaemikoMixed.safetensors",
    #       "preview_destination": "/Users/alexander/Projects/Python/mo_files/models/VAE/yaeMikoRealistic_yaemikoMixed.safetensors",
    #       "preview_dl": {
    #         "bytes_ready": 0,
    #         "bytes_total": 0,
    #         "speed_rate": 0,
    #         "elapsed": 0
    #       }
    #     }
    #   }
    # }

    DownloadManager.instance().start_download(records)

    while DownloadManager.instance().is_running():
        general_state = DownloadManager.instance().get_state()
        logger.debug('Total state: %s', general_state)
        logger.info('-T-> %s', _generate_js_general_update(general_state))

        latest_state = DownloadManager.instance().get_latest_state()
        logger.debug('Latest state: %s', latest_state)
        logger.info('-L-> %s', _generate_js_general_update(latest_state))
        yield _build_update(
            progress_update=_generate_js_general_update(general_state)
        )
        time.sleep(0.2)

    logger.debug('Final state:')

    general_state = DownloadManager.instance().get_state()
    logger.debug('Total state: %s', general_state)
    logger.info('-T-> %s', _generate_js_general_update(general_state))

    latest_state = DownloadManager.instance().get_latest_state()
    logger.debug('Latest state: %s', latest_state)
    logger.info('-L-> %s', _generate_js_general_update(latest_state))
    yield _build_update(
        progress_update=_generate_js_general_update(general_state)
    )

    logger.debug('Completed.')

    yield _build_update()


def _on_id_change(data):
    logger.info(f'download id data changed = {data}')
    records = []
    record_id = nav.get_download_record_id(data)
    group = nav.get_download_group(data)

    if record_id is not None:
        records.append(env.storage.get_record_by_id(record_id))

    if group is not None:
        records.extend(env.storage.get_records_by_group(group))

    return [
        gr.HTML.update(value=styled.download_cards(records)),
        records
    ]


def _on_cancel_click():
    DownloadManager.instance().stop_download()


def download_ui_block():
    with gr.Blocks():
        download_state = gr.State(value=[])
        id_box = gr.Textbox()  # TODO Hide
        download_progress_box = gr.Textbox()  # TODO Hide
        gr.Markdown('## Downloads')
        status_message_widget = gr.HTML(visible=False)
        with gr.Row():
            gr.Markdown()
            back_button = gr.Button('Back', visible=True)
            start_button = gr.Button('Start Download', visible=True)
            cancel_button = gr.Button('Cancel Download', visible=False)
            gr.Markdown()
        gr.HTML('</hr>')
        html_widget = gr.HTML()

    id_box.change(_on_id_change, inputs=id_box, outputs=[html_widget, download_state])
    download_progress_box.change(fn=None, inputs=download_progress_box, _js='handleProgressUpdates')

    start_button.click(_on_start_click, inputs=download_state,
                       outputs=[status_message_widget, start_button, cancel_button, back_button, download_progress_box])

    cancel_button.click(_on_cancel_click)  # TODO on cancel clicked

    return id_box
