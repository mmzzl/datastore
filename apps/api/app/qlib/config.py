"""
Qlib Configuration Module

This module provides configuration constants and default settings
for Qlib integration with OpenClaw.
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class QlibConfig:
    """
    Qlib configuration settings.
    
    Attributes:
        provider_uri: Qlib data provider URI
        region: Market region (REG_CN for China)
        model_dir: Directory for storing trained models
        default_model_type: Default model type for training
        default_factor_type: Default factor type
        default_instruments: Default stock pool
        min_sharpe_ratio: Minimum Sharpe ratio for approval
        training_config: Training configuration
    """
    
    provider_uri: str = "./qlib_data/cn_data"
    region: str = "CN"
    model_dir: str = "./models"
    default_model_type: str = "lgbm"
    default_factor_type: str = "alpha158"
    default_instruments: str = "csi300"
    min_sharpe_ratio: float = 1.5
    
    training_config: Dict[str, Any] = field(default_factory=lambda: {
        "model_type": "lgbm",
        "factor_type": "alpha158",
        "start_time": "2015-01-01",
        "end_time": "2026-01-01",
    })
    
    prediction_config: Dict[str, Any] = field(default_factory=lambda: {
        "topk": 50,
        "n_drop": 0,
    })


CSI_300_STOCKS: List[str] = [
    "SH600000", "SH600004", "SH600009", "SH600010", "SH600011",
    "SH600012", "SH600015", "SH600016", "SH600018", "SH600019",
    "SH600020", "SH600021", "SH600023", "SH600025", "SH600026",
    "SH600027", "SH600028", "SH600029", "SH600030", "SH600031",
    "SH600033", "SH600036", "SH600037", "SH600038", "SH600039",
    "SH600048", "SH600050", "SH600061", "SH600066", "SH600068",
    "SH600069", "SH600070", "SH600079", "SH600085", "SH600089",
    "SH600095", "SH600096", "SH600100", "SH600104", "SH600109",
    "SH600111", "SH600112", "SH600115", "SH600118", "SH600119",
    "SH600121", "SH600122", "SH600123", "SH600125", "SH600126",
    "SH600127", "SH600128", "SH600129", "SH600131", "SH600132",
    "SH600133", "SH600135", "SH600136", "SH600138", "SH600141",
    "SH600143", "SH600146", "SH600148", "SH600149", "SH600150",
    "SH600153", "SH600155", "SH600157", "SH600158", "SH600159",
    "SH600160", "SH600161", "SH600162", "SH600163", "SH600166",
    "SH600167", "SH600168", "SH600169", "SH600170", "SH600171",
    "SH600172", "SH600176", "SH600177", "SH600178", "SH600183",
    "SH600184", "SH600185", "SH600186", "SH600187", "SH600188",
    "SH600189", "SH600190", "SH600191", "SH600192", "SH600193",
    "SH600195", "SH600196", "SH600197", "SH600198", "SH600199",
]

CSI_500_STOCKS: List[str] = [
    "SH600004", "SH600007", "SH600008", "SH600021", "SH600032",
    "SH600038", "SH600060", "SH600062", "SH600095", "SH600096",
    "SH600098", "SH600109", "SH600118", "SH600126", "SH600131",
    "SH600132", "SH600141", "SH600143", "SH600153", "SH600157",
    "SH600166", "SH600170", "SH600171", "SH600177", "SH600208",
    "SH600282", "SH600295", "SH600298", "SH600299", "SH600312",
    "SH600316", "SH600329", "SH600332", "SH600339", "SH600348",
    "SH600352", "SH600363", "SH600369", "SH600378", "SH600380",
    "SH600390", "SH600392", "SH600398", "SH600435", "SH600483",
    "SH600486", "SH600487", "SH600497", "SH600498", "SH600499",
    "SH600511", "SH600516", "SH600517", "SH600521", "SH600528",
    "SH600535", "SH600536", "SH600546", "SH600549", "SH600562",
    "SH600563", "SH600566", "SH600578", "SH600580", "SH600582",
    "SH600583", "SH600598", "SH600601", "SH600602", "SH600606",
    "SH600637", "SH600642", "SH600655", "SH600663", "SH600673",
    "SH600685", "SH600688", "SH600699", "SH600704", "SH600707",
    "SH600720", "SH600737", "SH600739", "SH600754", "SH600763",
    "SH600764", "SH600765", "SH600801", "SH600808", "SH600816",
    "SH600820", "SH600848", "SH600862", "SH600863", "SH600871",
    "SH600873", "SH600879", "SH600884", "SH600885", "SH600901",
    "SH600906", "SH600909", "SH600927", "SH600959", "SH600967",
    "SH600968", "SH600970", "SH600977", "SH600985", "SH600988",
    "SH600995", "SH600998", "SH601000", "SH601001", "SH601016",
    "SH601019", "SH601061", "SH601098", "SH601099", "SH601106",
    "SH601108", "SH601118", "SH601128", "SH601139", "SH601155",
    "SH601156", "SH601162", "SH601168", "SH601179", "SH601198",
    "SH601212", "SH601216", "SH601228", "SH601231", "SH601233",
    "SH601333", "SH601399", "SH601555", "SH601567", "SH601577",
    "SH601598", "SH601608", "SH601611", "SH601615", "SH601665",
    "SH601666", "SH601696", "SH601699", "SH601717", "SH601799",
    "SH601865", "SH601866", "SH601880", "SH601918", "SH601921",
    "SH601928", "SH601958", "SH601965", "SH601966", "SH601990",
    "SH601991", "SH601997", "SH603000", "SH603049", "SH603077",
    "SH603087", "SH603129", "SH603156", "SH603160", "SH603179",
    "SH603225", "SH603228", "SH603233", "SH603290", "SH603298",
    "SH603338", "SH603341", "SH603345", "SH603379", "SH603444",
    "SH603486", "SH603529", "SH603565", "SH603568", "SH603589",
    "SH603596", "SH603605", "SH603606", "SH603650", "SH603658",
    "SH603659", "SH603688", "SH603699", "SH603707", "SH603728",
    "SH603737", "SH603766", "SH603786", "SH603806", "SH603816",
    "SH603833", "SH603858", "SH603885", "SH603899", "SH603920",
    "SH603927", "SH603939", "SH603979", "SH605358", "SH605589",
    "SH688002", "SH688017", "SH688018", "SH688019", "SH688027",
    "SH688037", "SH688052", "SH688065", "SH688099", "SH688100",
    "SH688114", "SH688120", "SH688122", "SH688166", "SH688172",
    "SH688180", "SH688183", "SH688188", "SH688192", "SH688213",
    "SH688220", "SH688234", "SH688235", "SH688248", "SH688266",
    "SH688278", "SH688281", "SH688295", "SH688297", "SH688301",
    "SH688318", "SH688322", "SH688336", "SH688347", "SH688349",
    "SH688361", "SH688363", "SH688375", "SH688385", "SH688387",
    "SH688425", "SH688469", "SH688475", "SH688520", "SH688525",
    "SH688538", "SH688561", "SH688563", "SH688568", "SH688578",
    "SH688582", "SH688599", "SH688608", "SH688615", "SH688617",
    "SH688629", "SH688676", "SH688692", "SH688702", "SH688709",
    "SH688728", "SH688772", "SH688777", "SH688778", "SH688819",
    "SH689009", "SZ000009", "SZ000021", "SZ000027", "SZ000032",
    "SZ000034", "SZ000039", "SZ000050", "SZ000060", "SZ000062",
    "SZ000088", "SZ000155", "SZ000400", "SZ000415", "SZ000423",
    "SZ000426", "SZ000429", "SZ000513", "SZ000519", "SZ000528",
    "SZ000537", "SZ000539", "SZ000559", "SZ000563", "SZ000582",
    "SZ000591", "SZ000598", "SZ000623", "SZ000629", "SZ000657",
    "SZ000683", "SZ000703", "SZ000709", "SZ000723", "SZ000728",
    "SZ000729", "SZ000733", "SZ000738", "SZ000739", "SZ000750",
    "SZ000783", "SZ000785", "SZ000825", "SZ000830", "SZ000831",
    "SZ000878", "SZ000883", "SZ000887", "SZ000893", "SZ000898",
    "SZ000921", "SZ000932", "SZ000933", "SZ000937", "SZ000951",
    "SZ000958", "SZ000959", "SZ000960", "SZ000967", "SZ000987",
    "SZ000997", "SZ001213", "SZ001221", "SZ001286", "SZ001389",
    "SZ001696", "SZ002007", "SZ002008", "SZ002025", "SZ002032",
    "SZ002044", "SZ002056", "SZ002064", "SZ002065", "SZ002078",
    "SZ002080", "SZ002085", "SZ002120", "SZ002126", "SZ002128",
    "SZ002130", "SZ002131", "SZ002138", "SZ002152", "SZ002153",
    "SZ002155", "SZ002156", "SZ002157", "SZ002185", "SZ002195",
    "SZ002202", "SZ002203", "SZ002223", "SZ002244", "SZ002261",
    "SZ002262", "SZ002265", "SZ002266", "SZ002271", "SZ002273",
    "SZ002281", "SZ002294", "SZ002299", "SZ002312", "SZ002318",
    "SZ002335", "SZ002340", "SZ002353", "SZ002372", "SZ002385",
    "SZ002402", "SZ002409", "SZ002410", "SZ002414", "SZ002423",
    "SZ002429", "SZ002430", "SZ002432", "SZ002436", "SZ002439",
    "SZ002444", "SZ002461", "SZ002465", "SZ002472", "SZ002500",
    "SZ002508", "SZ002517", "SZ002532", "SZ002558", "SZ002568",
    "SZ002583", "SZ002595", "SZ002603", "SZ002607", "SZ002608",
    "SZ002624", "SZ002670", "SZ002673", "SZ002683", "SZ002738",
    "SZ002739", "SZ002756", "SZ002773", "SZ002797", "SZ002821",
    "SZ002831", "SZ002837", "SZ002841", "SZ002850", "SZ002851",
    "SZ002926", "SZ002939", "SZ002945", "SZ002958", "SZ002966",
    "SZ002984", "SZ003021", "SZ003022", "SZ003031", "SZ003035",
    "SZ300001", "SZ300002", "SZ300003", "SZ300012", "SZ300017",
    "SZ300024", "SZ300037", "SZ300054", "SZ300058", "SZ300070",
    "SZ300073", "SZ300100", "SZ300115", "SZ300136", "SZ300140",
    "SZ300142", "SZ300144", "SZ300146", "SZ300207", "SZ300223",
    "SZ300285", "SZ300339", "SZ300346", "SZ300373", "SZ300383",
    "SZ300390", "SZ300395", "SZ300432", "SZ300450", "SZ300454",
    "SZ300458", "SZ300474", "SZ300487", "SZ300496", "SZ300529",
    "SZ300558", "SZ300567", "SZ300570", "SZ300601", "SZ300604",
    "SZ300623", "SZ300627", "SZ300676", "SZ300677", "SZ300679",
    "SZ300699", "SZ300718", "SZ300724", "SZ300735", "SZ300748",
    "SZ300751", "SZ300757", "SZ300763", "SZ300857", "SZ300888",
    "SZ300919", "SZ300957", "SZ300972", "SZ301200", "SZ301301",
    "SZ301308", "SZ301358", "SZ301498", "SZ301536", "SZ301611",
]


DEFAULT_MODEL_CONFIG: Dict[str, Any] = {
    "lgbm": {
        "class": "qlib.contrib.model.gbdt.LGBModel",
        "module_path": "qlib.contrib.model.gbdt",
        "kwargs": {
            "loss": "mse",
            "colsample_bytree": 0.8,
            "learning_rate": 0.01,
            "n_estimators": 1000,
            "num_leaves": 63,
            "subsample": 0.8,
            "early_stopping_rounds": 50,
        },
    },
    "mlp": {
        "class": "qlib.contrib.model.pytorch_mlp.PytorchMLPModel",
        "module_path": "qlib.contrib.model.pytorch_mlp",
        "kwargs": {
            "hidden_sizes": [256, 128, 64],
            "lr": 0.001,
            "batch_size": 4096,
            "epochs": 100,
        },
    },
}


DEFAULT_FACTOR_CONFIG: Dict[str, Any] = {
    "alpha158": {
        "class": "qlib.contrib.data.handler.Alpha158",
        "module_path": "qlib.contrib.data.handler",
    },
    "alpha360": {
        "class": "qlib.contrib.data.handler.Alpha360",
        "module_path": "qlib.contrib.data.handler",
    },
}


TRAINING_TIME_SEGMENTS: Dict[str, tuple] = {
    "train": ("2015-01-01", "2022-12-31"),
    "valid": ("2023-01-01", "2024-06-30"),
    "test": ("2024-07-01", "2026-01-01"),
}


CRON_SCHEDULES: Dict[str, str] = {
    "weekly_training": "0 2 * * 0",
    "daily_risk_report": "30 15 * * 1-5",
}


def get_model_config(model_type: str) -> Dict[str, Any]:
    """
    Get model configuration by type.
    
    Args:
        model_type: Model type identifier
    
    Returns:
        Model configuration dictionary
    """
    return DEFAULT_MODEL_CONFIG.get(model_type, DEFAULT_MODEL_CONFIG["lgbm"])


def get_factor_config(factor_type: str) -> Dict[str, Any]:
    """
    Get factor configuration by type.
    
    Args:
        factor_type: Factor type identifier
    
    Returns:
        Factor configuration dictionary
    """
    return DEFAULT_FACTOR_CONFIG.get(factor_type, DEFAULT_FACTOR_CONFIG["alpha158"])


def get_csi300_instruments() -> List[str]:
    """Get CSI 300 stock list.

    Returns:
        List of stock codes
    """
    return CSI_300_STOCKS.copy()


def get_csi500_instruments() -> List[str]:
    """Get CSI 500 stock list.

    Returns:
        List of stock codes
    """
    return CSI_500_STOCKS.copy()


VALID_POOLS = {"csi300", "csi500"}


def get_instruments(pool_name: str) -> List[str]:
    """Get stock list by pool name.

    Args:
        pool_name: Stock pool name, either "csi300" or "csi500"

    Returns:
        List of stock codes

    Raises:
        ValueError: If pool_name is not a valid pool name
    """
    if pool_name == "csi300":
        return get_csi300_instruments()
    elif pool_name == "csi500":
        return get_csi500_instruments()
    else:
        raise ValueError(
            f"Invalid pool name: '{pool_name}'. Valid pool names: {sorted(VALID_POOLS)}"
        )


def create_dataset_config(
    instruments: List[str],
    start_time: str,
    end_time: str,
    factor_type: str = "alpha158",
    train_ratio: float = 0.6,
    valid_ratio: float = 0.2,
) -> Dict[str, Any]:
    """
    Create Qlib Dataset configuration.
    
    Args:
        instruments: List of stock codes
        start_time: Start date
        end_time: End date
        factor_type: Factor type (alpha158, alpha360)
        train_ratio: Training data ratio
        valid_ratio: Validation data ratio
    
    Returns:
        Dataset configuration dictionary
    """
    factor_config = get_factor_config(factor_type)
    
    from datetime import datetime
    import pandas as pd
    
    start_dt = pd.to_datetime(start_time)
    end_dt = pd.to_datetime(end_time)
    total_days = (end_dt - start_dt).days
    
    train_end = start_dt + pd.Timedelta(days=int(total_days * train_ratio))
    valid_end = start_dt + pd.Timedelta(days=int(total_days * (train_ratio + valid_ratio)))
    
    return {
        "class": "qlib.data.dataset.DatasetH",
        "module_path": "qlib.data.dataset",
        "kwargs": {
            "handler": {
                **factor_config,
                "kwargs": {
                    "start_time": start_time,
                    "end_time": end_time,
                    "fit_start_time": start_time,
                    "fit_end_time": end_time,
                    "instruments": instruments,
                },
            },
            "segments": {
                "train": (start_time, train_end.strftime("%Y-%m-%d")),
                "valid": (train_end.strftime("%Y-%m-%d"), valid_end.strftime("%Y-%m-%d")),
                "test": (valid_end.strftime("%Y-%m-%d"), end_time),
            },
        },
    }
