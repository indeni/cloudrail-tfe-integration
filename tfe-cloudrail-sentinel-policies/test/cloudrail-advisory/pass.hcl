mock "tfconfig" {
  module {
    source = "../../mock/pass/mock-tfconfig.sentinel"
  }
}

mock "tfconfig/v1" {
  module {
    source = "../../mock/pass/mock-tfconfig.sentinel"
  }
}

mock "tfconfig/v2" {
  module {
    source = "../../mock/pass/mock-tfconfig-v2.sentinel"
  }
}

mock "tfplan" {
  module {
    source = "../../mock/pass/mock-tfplan.sentinel"
  }
}

mock "tfplan/v1" {
  module {
    source = "../../mock/pass/mock-tfplan.sentinel"
  }
}

mock "tfplan/v2" {
  module {
    source = "../../mock/pass/mock-tfplan-v2.sentinel"
  }
}

mock "tfstate" {
  module {
    source = "../../mock/pass/mock-tfstate.sentinel"
  }
}

mock "tfstate/v1" {
  module {
    source = "../../mock/pass/mock-tfstate.sentinel"
  }
}

mock "tfstate/v2" {
  module {
    source = "../../mock/pass/mock-tfstate-v2.sentinel"
  }
}

mock "tfrun" {
  module {
    source = "../../mock/pass/mock-tfrun.sentinel"
  }
}

test {
    rules = {
        main = true
    }
    
}

param "CLOUDRAIL_API_KEY" {
  value = "_-v_D8mNNXDNs_qoxMsxaAVlRhAaAtMS_B4NAfQO964"
}