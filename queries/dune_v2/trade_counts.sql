-- V2 Query: https://dune.com/queries/1393633?d=1
select solver,
       count(*) as num_trades
from gnosis_protocol_v2_ethereum.GPv2Settlement_evt_Trade t
         join gnosis_protocol_v2_ethereum.GPv2Settlement_evt_Settlement s
              on t.evt_tx_hash = s.evt_tx_hash
where t.evt_block_number between {{start_block}} and {{end_block}}
group by solver
order by num_trades desc, solver