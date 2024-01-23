#include <stdio.h>
#define PROD_EI_ENABLED // For using EI_Config_t
#define PROD_NUM_PS_CPU_ACTIVE (2)
#define WINFW
#define STAT
#define BYPASS_SET_APIS
#define RAM_ADDRESS(...) (0)
#define ASIC_FIMS (8)
#define PROD_BICS6_EX3
#define PROD_ATLASR_PRE_ERASE // It need to check EI_config.h (24.01.18)
#define _CRT_SECURE_NO_WARNINGS

#include "SYS_GlobalTypes.h"
uint32_t PS_Instance;
#include "SYS_Globals.h"
#include "EI_config.h"

// build command : 
// gcc main.c -save-temps -I..\..\..\Source\Infra\BSP\inc_public -I..\..\..\Source\Infra\inc_public -I..\..\..\Source\PS\inc_public -I..\..\..\Source\FTL\inc_public -I..\..\..\Source\Infra\CfgManager\inc_public -I..\..\..\WinFw\Firmware\Stubs

int main(void)
{
	EI_Config_t *pConfig;
	uint16_t hi;
	printf("hello\n");
}