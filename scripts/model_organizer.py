import gradio as gr

from modules import script_callbacks
from modules import shared, sd_models, sd_vae
from modules.shared import OptionInfo

from scripts.mo.environment import env, STORAGE_SQLITE, STORAGE_NOTION
from scripts.mo.ui_main import main_ui_block

env.mo_storage_type = lambda: shared.opts.mo_storage_type
env.mo_notion_api_token = lambda: shared.opts.mo_notion_api_token
env.mo_notion_db_id = lambda: shared.opts.mo_notion_db_id
env.mo_model_path = lambda: shared.opts.mo_model_path
env.mo_vae_path = lambda: shared.opts.mo_vae_path
env.mo_lora_path = lambda: shared.opts.mo_lora_path
env.mo_hypernetworks_path = lambda: shared.opts.mo_hypernetworks_path
env.mo_embeddings_path = lambda: shared.opts.mo_embeddings_path


def on_ui_settings():
    model_path = sd_models.model_path
    vae_path = sd_vae.vae_path
    lora_path = shared.cmd_opts.lora_dir
    hypernetworks_path = shared.cmd_opts.hypernetwork_dir
    embeddings_path = shared.cmd_opts.embeddings_dir

    mo_options = shared.options_section(('mo', 'Model Organizer'), {
        'mo_storage_type': OptionInfo(STORAGE_SQLITE, "Storage Type:", gr.Radio,
                                   {"choices": [STORAGE_SQLITE, STORAGE_NOTION]}),
        'mo_notion_api_token': OptionInfo('', 'Notion API Token:'),
        'mo_notion_db_id': OptionInfo('', 'Notion Database Id:'),

        'mo_model_path': OptionInfo('', f'Model directory (If empty uses default: {model_path}):'),
        'mo_vae_path': OptionInfo('', f'VAE directory (If empty uses default: {vae_path}) :'),
        'mo_lora_path': OptionInfo('', f'Lora directory (If empty uses default: {lora_path}):'),
        'mo_hypernetworks_path': OptionInfo('',
                                            f'Hypernetworks directory (If empty uses default: {hypernetworks_path}):'),
        'mo_embeddings_path': OptionInfo('', f'Embeddings directory (If empty uses default: {embeddings_path}):')
    })
    shared.options_templates.update(mo_options)


def on_ui_tabs():
    return (main_ui_block(), "Model Organizer", "model_organizer"),


script_callbacks.on_ui_settings(on_ui_settings)
script_callbacks.on_ui_tabs(on_ui_tabs)
