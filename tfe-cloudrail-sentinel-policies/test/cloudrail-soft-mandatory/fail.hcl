mock "tfconfig" {
  module {
    source = "../../mock/fail/mock-tfconfig.sentinel"
  }
}

mock "tfconfig/v1" {
  module {
    source = "../../mock/fail/mock-tfconfig.sentinel"
  }
}

mock "tfconfig/v2" {
  module {
    source = "../../mock/fail/mock-tfconfig-v2.sentinel"
  }
}

mock "tfplan" {
  module {
    source = "../../mock/fail/mock-tfplan.sentinel"
  }
}

mock "tfplan/v1" {
  module {
    source = "../../mock/fail/mock-tfplan.sentinel"
  }
}

mock "tfplan/v2" {
  module {
    source = "../../mock/fail/mock-tfplan-v2.sentinel"
  }
}

mock "tfstate" {
  module {
    source = "../../mock/fail/mock-tfstate.sentinel"
  }
}

mock "tfstate/v1" {
  module {
    source = "../../mock/fail/mock-tfstate.sentinel"
  }
}

mock "tfstate/v2" {
  module {
    source = "../../mock/fail/mock-tfstate-v2.sentinel"
  }
}

mock "tfrun" {
  module {
    source = "../../mock/fail/mock-tfrun.sentinel"
  }
}

test {
    rules = {
        main = true
    }
    
}

param "cloudrailToken" {
  value = "_-v_D8mNNXDNs_qoxMsxaAVlRhAaAtMS_B4NAfQO964"
}